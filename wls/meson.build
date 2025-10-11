# Instala as dependências Python dos wheels
python = import('python').find_installation('python3')

# Instala cada wheel
wheels = [
  'beautifulsoup4-4.14.2-py3-none-any.whl',
  'certifi-2025.10.5-py3-none-any.whl',
  'cffi-2.0.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl',
  'charset_normalizer-3.4.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl',
  'curl_cffi-0.13.0-cp39-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl',
  'idna-3.10-py3-none-any.whl',
  'lxml-6.0.2-cp312-cp312-manylinux_2_26_x86_64.manylinux_2_28_x86_64.whl',
  'numpy-2.3.3-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl',
  'pandas-2.3.3-cp312-cp312-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl',
  'pycparser-2.23-py3-none-any.whl',
  'python_dateutil-2.9.0.post0-py2.py3-none-any.whl',
  'pytz-2025.2-py2.py3-none-any.whl',
  'requests-2.32.5-py3-none-any.whl',
  'requests_futures-1.0.2-py2.py3-none-any.whl',
  'six-1.17.0-py2.py3-none-any.whl',
  'soupsieve-2.8-py3-none-any.whl',
  'tqdm-4.67.1-py3-none-any.whl',
  'typing_extensions-4.15.0-py3-none-any.whl',
  'tzdata-2025.2-py2.py3-none-any.whl',
  'urllib3-2.5.0-py3-none-any.whl',
  'yahooquery-2.4.1-py3-none-any.whl',
]

wheels_dir = meson.current_source_dir()

foreach wheel : wheels
  wheel_path = wheels_dir / wheel
  meson.add_install_script('sh', '-c',
    'pip3 install --no-index --find-links=@0@ --prefix=$DESTDIR@1@ --no-build-isolation @2@'.format(wheels_dir, get_option('prefix'), wheel_path)
  )
endforeach