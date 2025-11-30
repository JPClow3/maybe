"""
Service for creating pre-configured rules for Brazilian services
"""
from finance.models import Rule, RuleCondition, RuleAction, Category


class BrazilianRulePresets:
    """Pre-configured rules for common Brazilian services"""
    
    # Common Brazilian service patterns
    PRESETS = [
        {
            'name': 'Uber - Transporte',
            'pattern': r'.*UBER.*',
            'category_name': 'Transporte',
            'description': 'Categoriza corridas do Uber como Transporte'
        },
        {
            'name': '99 - Transporte',
            'pattern': r'.*99.*',
            'category_name': 'Transporte',
            'description': 'Categoriza corridas do 99 como Transporte'
        },
        {
            'name': 'iFood - Alimentação',
            'pattern': r'.*IFOOD.*',
            'category_name': 'Alimentação',
            'description': 'Categoriza pedidos do iFood como Alimentação'
        },
        {
            'name': 'Rappi - Alimentação',
            'pattern': r'.*RAPPI.*',
            'category_name': 'Alimentação',
            'description': 'Categoriza pedidos do Rappi como Alimentação'
        },
        {
            'name': 'Nubank - Taxa',
            'pattern': r'.*NUBANK.*TAXA.*',
            'category_name': 'Taxas',
            'description': 'Categoriza taxas do Nubank'
        },
        {
            'name': 'Netflix - Entretenimento',
            'pattern': r'.*NETFLIX.*',
            'category_name': 'Entretenimento',
            'description': 'Categoriza assinatura Netflix'
        },
        {
            'name': 'Spotify - Entretenimento',
            'pattern': r'.*SPOTIFY.*',
            'category_name': 'Entretenimento',
            'description': 'Categoriza assinatura Spotify'
        },
    ]
    
    @classmethod
    def create_preset_rules(cls, user):
        """
        Create preset rules for a user
        
        Args:
            user: User instance
            
        Returns:
            List of created Rule instances
        """
        created_rules = []
        
        for preset in cls.PRESETS:
            # Get or create category
            category, _ = Category.objects.get_or_create(
                user=user,
                name=preset['category_name'],
                defaults={'classification': 'expense'}
            )
            
            # Check if rule already exists
            existing_rule = Rule.objects.filter(
                user=user,
                name=preset['name']
            ).first()
            
            if existing_rule:
                continue  # Skip if rule already exists
            
            # Create rule
            rule = Rule.objects.create(
                user=user,
                name=preset['name']
            )
            
            # Create condition (regex pattern)
            RuleCondition.objects.create(
                rule=rule,
                condition_type='transaction_name',
                operator='regex',
                value=preset['pattern']
            )
            
            # Create action (set category)
            RuleAction.objects.create(
                rule=rule,
                action_type='set_transaction_category',
                value=str(category.id)
            )
            
            created_rules.append(rule)
        
        return created_rules
    
    @classmethod
    def suggest_category(cls, transaction_name):
        """
        Suggest category based on transaction name patterns
        
        Args:
            transaction_name: Name of the transaction
            
        Returns:
            Suggested category name or None
        """
        import re
        
        transaction_upper = transaction_name.upper()
        
        for preset in cls.PRESETS:
            pattern = preset['pattern']
            if re.match(pattern, transaction_upper, re.IGNORECASE):
                return preset['category_name']
        
        return None

