from setuptools import setup, find_packages

setup(
    name='aeronet_visui',
    version='1.0.0',
    packages=find_packages(exclude=['build']),
    package_data={'': ['*.so']},
    #     # If any package contains *.txt files, include them:
    #     '': ['*.txt'],
    #     'lut': ['data/lut/*.nc'],
    #     'aux': ['data/aux/*']
    # },
    include_package_data=True,

    url='https://github.com/Tristanovsk/aeronet_visu',
    license='MIT',
    author='T. Harmel',
    author_email='tristan.harmel@ntymail.com',
    description='Visualization tool for AERONET / AERONET-OC data',
    # TODO update Dependent packages (distributions)
    install_requires=['dash','dash_core_components','dash_html_components','dash_table_experiments','flask','flask_caching',
                      'pandas', 'scipy', 'numpy', 'matplotlib', 'plotly'],

    entry_points={
        'console_scripts': [
            'aeronet_visu = aeronet_visu.visu_main:main'
        ]}
)