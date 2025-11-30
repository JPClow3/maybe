module.exports = {
  ci: {
    collect: {
      url: [
        'http://localhost:8000/login/',
        'http://localhost:8000/register/',
      ],
      numberOfRuns: 3,
    },
    assert: {
      assertions: {
        'categories:performance': ['error', { minScore: 0.90 }],
        'categories:accessibility': ['error', { minScore: 0.90 }],
        'categories:best-practices': ['error', { minScore: 0.80 }],
        'categories:seo': ['error', { minScore: 0.80 }],
      },
    },
    upload: {
      target: 'filesystem',
      outputDir: '.lighthouseci',
    },
  },
};

