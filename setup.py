from setuptools import setup

execfile('novelty_targeting/version.py')

setup(
    name='novelty_targeting',
    version=__version__,
    description='Novelty Targeting',
    url='https://github.jpl.nasa.gov/wkiri/novelty-targeting',
    author='CIF novelty targeting team',
    author_email='cif-novelty@jpl.nasa.gov',
    packages=['novelty_targeting'],
    install_requires=[
        'matplotlib==2.2.3',
        'numpy==1.15.4',
        'scipy==1.1.0',
        'scikit-image==0.14.1',
        'scikit-learn==0.20.4',
        'progressbar==2.3',
        'six==1.11.0',
        'Pillow==6.2.1',
        'planetaryimage==0.5.0',
        'pytest==4.6.11',
        'PyYAML==5.4.1'
    ],
    provide=[
        'novelty_targeting'
    ],
    entry_points={
        'console_scripts': [
            'demud_ranking = novelty_targeting.demud_ranking:main',
            'iforest_ranking = novelty_targeting.iforest_ranking:main',
            'pca_ranking = novelty_targeting.pca_ranking:main',
            'rx_ranking = novelty_targeting.rx_ranking:main',
            'random_ranking = novelty_targeting.random_ranking:main',
            'aegis_ranking = novelty_targeting.aegis_ranking:main',
            'lrx_ranking = novelty_targeting.lrx_ranking:main',
            'run_exp = novelty_targeting.run_exp:main',
            'simulator = novelty_targeting.simulator:main'
        ]
    },
    include_package_data=True
)
