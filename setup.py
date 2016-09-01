import distutils.core


distutils.core.setup(
    name='customlogging',
    packages=['customlogging', 'tests'],
    version='0.1.8',
    description='A set of custom logging wrappers and functions.',
    author='Mat Lee',
    author_email='matt@lumidatum.com',
    url='',
    download_url='',
    keywords=['logging', 'machine learning'],
    classifiers=[],
    install_requires=[
        'requests',
    ]
)
