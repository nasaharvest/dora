from setuptools import setup

exec(open('dora_exp_pipeline/version.py').read())

setup(
    name='dora_exp_pipeline',
    version=__version__,
    description='DORA Experiment Pipeline',
    url='https://github.com/nasaharvest/dora',
    author='DORA team',
    author_email='you.lu@jpl.nasa.gov',
    packages=['dora_exp_pipeline'],
    install_requires=[
        'matplotlib==3.4.2',
        'numpy==1.20.3',
        'scipy==1.6.3',
        'scikit-image==0.18.1',
        'scikit-learn==0.24.2',
        'Pillow==8.2.0',
        'planetaryimage==0.5.0',
        'PyYAML==5.4.1'
    ],
    provide=[
        'dora_exp_pipeline'
    ],
    entry_points={
        'console_scripts': [
            'dora_exp = dora_exp_pipeline.dora_exp:main'
        ]
    },
    include_package_data=True
)
