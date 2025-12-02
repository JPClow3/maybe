"""
Balance calculator - ported from app/models/balance/base_calculator.rb
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
from django.utils import timezone
from finance.models import Account, Balance, Valuation, Transaction
from investments.models import Holding, Trade
from .sync_cache import SyncCache


class BaseBalanceCalculator:
    """Base class for balance calculators"""
    
    def __init__(self, account: Account):
        self.account = account
        self._sync_cache = None
    
    def calculate(self) -> List[Balance]:
        """Calculate balances - must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement calculate()")
    
    @property
    def sync_cache(self) -> SyncCache:
        """Get or create sync cache"""
        if self._sync_cache is None:
            self._sync_cache = SyncCache(self.account)
        return self._sync_cache
    
    def holdings_value_for_date(self, target_date: date) -> Decimal:
        """Calculate total holdings value for a date"""
        holdings = self.sync_cache.get_holdings(target_date)
        return sum(h.amount for h in holdings if h.amount is not None) or Decimal('0')
    
    def derive_cash_balance_on_date_from_total(self, total_balance: Decimal, target_date: date) -> Decimal:
        """Derive cash balance from total balance"""
        if self.account.accountable_type == 'investment':
            return total_balance - self.holdings_value_for_date(target_date)
        elif self.account.accountable_type in ['depository', 'credit_card']:
            return total_balance
        else:
            return Decimal('0')
    
    def flows_for_date(self, target_date: date) -> Dict[str, Decimal]:
        """Calculate cash and non-cash flows for a date"""
        entries = self.sync_cache.get_entries(target_date)
        
        cash_inflows = Decimal('0')
        cash_outflows = Decimal('0')
        non_cash_inflows = Decimal('0')
        non_cash_outflows = Decimal('0')
        
        # Separate transactions and trades
        transactions = [e for e in entries if isinstance(e, Transaction)]
        trades = [e for e in entries if isinstance(e, Trade)]
        
        # Transaction flows
        txn_inflow_sum = sum(t.amount for t in transactions if t.amount < 0)
        txn_outflow_sum = sum(t.amount for t in transactions if t.amount >= 0)
        
        # Trade flows (trades affect cash and holdings)
        trade_cash_inflow_sum = sum(t.amount for t in trades if t.amount < 0)
        trade_cash_outflow_sum = sum(t.amount for t in trades if t.amount >= 0)
        
        # Loans are special case
        if self.account.accountable_type == 'loan':
            non_cash_inflows = abs(txn_inflow_sum)
            non_cash_outflows = txn_outflow_sum
        else:
            # Cash flows
            cash_inflows = abs(txn_inflow_sum) + abs(trade_cash_inflow_sum)
            cash_outflows = txn_outflow_sum + trade_cash_outflow_sum
            
            # Non-cash flows (trades are inverse for holdings)
            non_cash_outflows = abs(trade_cash_inflow_sum)
            non_cash_inflows = trade_cash_outflow_sum
        
        return {
            'cash_inflows': cash_inflows,
            'cash_outflows': cash_outflows,
            'non_cash_inflows': non_cash_inflows,
            'non_cash_outflows': non_cash_outflows,
        }
    
    def market_value_change_on_date(self, target_date: date, flows: Dict[str, Decimal]) -> Decimal:
        """Calculate market value change (for investment accounts)"""
        if self.account.accountable_type != 'investment':
            return Decimal('0')
        
        prev_date = target_date - timedelta(days=1)
        start_holdings_value = self.holdings_value_for_date(prev_date)
        end_holdings_value = self.holdings_value_for_date(target_date)
        
        change_holdings_value = end_holdings_value - start_holdings_value
        net_buy_sell_value = flows['non_cash_inflows'] - flows['non_cash_outflows']
        
        return change_holdings_value - net_buy_sell_value
    
    def build_balance(self, target_date: date, **kwargs) -> Balance:
        """Build a Balance instance"""
        flows_factor = 1 if self.account.classification == 'asset' else -1
        
        return Balance(
            account=self.account,
            date=target_date,
            currency=self.account.currency,
            balance=kwargs.get('balance', Decimal('0')),
            cash_balance=kwargs.get('cash_balance', Decimal('0')),
            start_cash_balance=kwargs.get('start_cash_balance', Decimal('0')),
            start_non_cash_balance=kwargs.get('start_non_cash_balance', Decimal('0')),
            cash_inflows=kwargs.get('cash_inflows', Decimal('0')),
            cash_outflows=kwargs.get('cash_outflows', Decimal('0')),
            non_cash_inflows=kwargs.get('non_cash_inflows', Decimal('0')),
            non_cash_outflows=kwargs.get('non_cash_outflows', Decimal('0')),
            net_market_flows=kwargs.get('net_market_flows', Decimal('0')),
            cash_adjustments=kwargs.get('cash_adjustments', Decimal('0')),
            non_cash_adjustments=kwargs.get('non_cash_adjustments', Decimal('0')),
            flows_factor=flows_factor,
        )
    
    def get_opening_anchor(self) -> Optional[Valuation]:
        """Get opening anchor valuation"""
        return Valuation.objects.filter(
            account=self.account,
            kind='reconciliation'  # Simplified - use reconciliation as opening
        ).order_by('date').first()
    
    def get_opening_anchor_balance(self) -> Decimal:
        """Get opening anchor balance"""
        opening = self.get_opening_anchor()
        if opening:
            return opening.amount
        # If no valuation, use account's balance as initial balance
        # This handles accounts created with an initial balance
        return self.account.balance or Decimal('0')
    
    def get_opening_anchor_date(self) -> date:
        """Get opening anchor date"""
        opening = self.get_opening_anchor()
        if opening:
            return opening.date
        
        # Fallback to oldest transaction date - 1 day
        oldest_txn = Transaction.objects.filter(account=self.account).order_by('date').first()
        if oldest_txn:
            return oldest_txn.date - timedelta(days=1)
        
        # If no transactions, use account creation date or today - 1 day
        if hasattr(self.account, 'created_at') and self.account.created_at:
            return self.account.created_at.date() - timedelta(days=1)
        
        return timezone.now().date() - timedelta(days=1)


class ForwardBalanceCalculator(BaseBalanceCalculator):
    """Forward balance calculator - calculates from opening to current"""
    
    def calculate(self) -> List[Balance]:
        """Calculate balances forward from opening anchor"""
        start_date = self.get_opening_anchor_date()
        start_cash_balance = self.derive_cash_balance_on_date_from_total(
            total_balance=self.get_opening_anchor_balance(),
            target_date=start_date
        )
        start_non_cash_balance = self.get_opening_anchor_balance() - start_cash_balance
        
        # Calculate end date
        end_date = self._calc_end_date()
        
        if start_date > end_date:
            return []
        
        balances = []
        current_date = start_date
        
        while current_date <= end_date:
            valuation = self.sync_cache.get_valuation(current_date)
            
            if valuation:
                # Use valuation as end balance
                end_cash_balance = self.derive_cash_balance_on_date_from_total(
                    total_balance=valuation.amount,
                    target_date=current_date
                )
                end_non_cash_balance = valuation.amount - end_cash_balance
            else:
                # Calculate from flows
                end_cash_balance = self._derive_end_cash_balance(start_cash_balance, current_date)
                end_non_cash_balance = self._derive_end_non_cash_balance(start_non_cash_balance, current_date)
            
            flows = self.flows_for_date(current_date)
            market_value_change = self.market_value_change_on_date(current_date, flows)
            
            flows_factor = 1 if self.account.classification == 'asset' else -1
            net_cash_flows = (flows['cash_inflows'] - flows['cash_outflows']) * flows_factor
            net_non_cash_flows = (flows['non_cash_inflows'] - flows['non_cash_outflows']) * flows_factor
            
            cash_adjustments = self._cash_adjustments_for_date(
                start_cash_balance, end_cash_balance, net_cash_flows
            )
            non_cash_adjustments = self._non_cash_adjustments_for_date(
                start_non_cash_balance, end_non_cash_balance, net_non_cash_flows
            )
            
            balance = self.build_balance(
                target_date=current_date,
                balance=end_cash_balance + end_non_cash_balance,
                cash_balance=end_cash_balance,
                start_cash_balance=start_cash_balance,
                start_non_cash_balance=start_non_cash_balance,
                cash_inflows=flows['cash_inflows'],
                cash_outflows=flows['cash_outflows'],
                non_cash_inflows=flows['non_cash_inflows'],
                non_cash_outflows=flows['non_cash_outflows'],
                cash_adjustments=cash_adjustments,
                non_cash_adjustments=non_cash_adjustments,
                net_market_flows=market_value_change,
            )
            
            balances.append(balance)
            
            # Update for next iteration
            start_cash_balance = end_cash_balance
            start_non_cash_balance = end_non_cash_balance
            current_date += timedelta(days=1)
        
        return balances
    
    def _calc_end_date(self) -> date:
        """Calculate end date for balance calculation"""
        dates = []
        
        last_txn = Transaction.objects.filter(account=self.account).order_by('-date').first()
        if last_txn:
            dates.append(last_txn.date)
        
        last_trade = Trade.objects.filter(account=self.account).order_by('-date').first()
        if last_trade:
            dates.append(last_trade.date)
        
        last_holding = Holding.objects.filter(account=self.account).order_by('-date').first()
        if last_holding:
            dates.append(last_holding.date)
        
        if dates:
            return max(dates)
        
        return timezone.now().date()
    
    def _signed_entry_flows(self, entries: List) -> Decimal:
        """Calculate signed entry flows (negative = inflow for assets)"""
        total = sum(e.amount for e in entries)
        if self.account.classification == 'asset':
            return -total
        return total
    
    def _derive_end_cash_balance(self, start_cash_balance: Decimal, target_date: date) -> Decimal:
        """Derive end cash balance from start"""
        if self.account.accountable_type in ['loan', 'other_liability']:
            return Decimal('0')
        
        entries = self.sync_cache.get_entries(target_date)
        transactions = [e for e in entries if isinstance(e, Transaction)]
        trades = [e for e in entries if isinstance(e, Trade)]
        
        # Transactions affect cash
        txn_flows = self._signed_entry_flows(transactions)
        
        # Trades affect cash (buy = outflow, sell = inflow)
        trade_flows = self._signed_entry_flows(trades)
        
        return start_cash_balance + txn_flows + trade_flows
    
    def _derive_end_non_cash_balance(self, start_non_cash_balance: Decimal, target_date: date) -> Decimal:
        """Derive end non-cash balance from start"""
        if self.account.accountable_type == 'loan':
            entries = self.sync_cache.get_entries(target_date)
            transactions = [e for e in entries if isinstance(e, Transaction)]
            flows = self._signed_entry_flows(transactions)
            return start_non_cash_balance + flows
        elif self.account.accountable_type == 'investment':
            return self.holdings_value_for_date(target_date)
        else:
            return start_non_cash_balance
    
    def _cash_adjustments_for_date(self, start_cash: Decimal, end_cash: Decimal, net_flows: Decimal) -> Decimal:
        """Calculate cash adjustments"""
        if self.account.accountable_type in ['loan', 'other_liability']:
            return Decimal('0')
        return end_cash - start_cash - net_flows
    
    def _non_cash_adjustments_for_date(self, start_non_cash: Decimal, end_non_cash: Decimal, net_flows: Decimal) -> Decimal:
        """Calculate non-cash adjustments"""
        if self.account.accountable_type not in ['loan', 'other_liability']:
            return Decimal('0')
        return end_non_cash - start_non_cash - net_flows

