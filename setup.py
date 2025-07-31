from setuptools import setup
import sys

exec(open('dora_exp_pipeline/version.py').read())

# Default: Python 3.6 dependencies
install_requires = [
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
    'tensorflow-addons==0.13.0',
    'sklearn-som==1.1.0'
]

# For Python >= 3.8, upgrade to newer dependencies
if sys.version_info >= (3, 8):
    install_requires = [
        'matplotlib==3.7.5',
        'numpy==1.24.3',
        'scipy==1.9.1',
        'scikit-image==0.20.0',
        'scikit-learn==1.3.2',
        'Pillow==10.4.0',
        'planetaryimage==0.5.0',
        'PyYAML==6.0.2',
        'pandas==2.0.3',
        'rasterio==1.2.6',
        'tqdm==4.67.1',
        'tensorflow==2.13.0',
        'tensorflow-probability==0.21.0',
        'tensorflow-addons==0.21.0',
        'sklearn-som==1.1.0',
        'geopandas==0.9.0',
        'seaborn==0.13.2'
    ]

setup(
    name='dora_exp_pipeline',
    version=__version__,  # noqa: F821
    description='DORA Experiment Pipeline',
    url='https://github.com/nasaharvest/dora',
    author='DORA team',
    author_email='you.lu@jpl.nasa.gov',
    packages=['dora_exp_pipeline'],
    python_requires='>=3.6',
    install_requires=install_requires,
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
