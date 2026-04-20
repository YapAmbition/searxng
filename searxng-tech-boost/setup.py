from setuptools import setup

setup(
    name='searxng-tech-boost',
    version='0.1.0',
    description='SearXNG plugin to boost technical domains, filter low-quality sites, and add metadata',
    py_modules=['tech_boost'],
    entry_points={
        'searxng.plugins': [
            'tech-boost = tech_boost',
        ]
    }
)

