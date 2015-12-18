from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='pyslip',
      version='3.0.4',
      description='A slipmap widget for wxPython',
      long_description=readme(),
      url='http://github.com/rzzzwilson/pySlip',
      author='Ross Wilson',
      author_email='rzzzwilson@gmail.com',
      license='MIT',
      packages=['pyslip'],
      install_requires=['python', 'wxpython'],
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 2 :: Only'],
      keywords='python wxpython slipmap map',
      download_url='https://github.com/rzzzwilson/pySlip/releases/tag/3.0.4',
      include_package_data=True,
      zip_safe=False)
