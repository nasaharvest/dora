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
        'matplotlib==3.3.4',
        'numpy==1.19.5',
        'scipy==1.5.4',
        'scikit-image==0.17.2',
        'scikit-learn==0.24.2',
        'Pillow==8.2.0',
        'planetaryimage==0.5.0',
        'PyYAML==5.4.1',
        'pandas==1.1.5',
        'rasterio==1.2.6',
        'tqdm==4.62.0',
        'tensorflow==2.5.1',
        'tensorflow-probability==0.13.0',
        'tensorflow-addons==0.13.0'
        'sklearn-som==1.1.0'
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
