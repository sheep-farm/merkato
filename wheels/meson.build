python = import('python').find_installation('python3')
fs = import('fs')

# Lê o arquivo wheels_list.txt
wheels_file = join_paths(meson.current_source_dir(), '..\wheels_list.txt')
wheels_content = fs.read(wheels_file)

# Remove aspas simples, vírgulas e quebras de linha, depois separa em lista
wheels_raw = wheels_content.strip().replace('\'', '').replace(',', '')
wheels = wheels_raw.split()

wheels_dir = meson.current_source_dir()
wheel_paths = []
foreach w : wheels
  wheel_paths += [join_paths(wheels_dir, w)]
endforeach

wheels_str = ' '.join(wheel_paths)

meson.add_install_script(
  'sh', '-c',
  'pip3 install --upgrade --no-deps --target="$MESON_INSTALL_DESTDIR_PREFIX/lib/python3.12/site-packages" --no-cache-dir ' + wheels_str + ' && ' +
  'find "$MESON_INSTALL_DESTDIR_PREFIX" -type d -name tests -exec rm -rf {} + || true'
)