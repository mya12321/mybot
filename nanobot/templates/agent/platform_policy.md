{% if system == 'Windows' %}
<platform_policy os="Windows">
- Do not assume GNU tools like `grep`, `sed`, or `awk` exist.
- Prefer Windows-native commands or file tools when more reliable.
- On garbled terminal output, retry with UTF-8 output enabled.
</platform_policy>
{% else %}
<platform_policy os="POSIX">
- Prefer UTF-8 and standard shell tools.
- Use file tools when simpler or more reliable than shell commands.
</platform_policy>
{% endif %}