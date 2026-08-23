import json
import subprocess

try:
    result = subprocess.run(
        ["curl", "-s", "--max-time", "8", "wttr.in/Carleton+Place,ON?format=j1"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    data = json.loads(result.stdout)
    cur = data["current_condition"][0]
    temp = cur["temp_C"]
    feels = cur["FeelsLikeC"]
    desc = cur["weatherDesc"][0]["value"].strip()
    humidity = cur["humidity"]

    print(
        f"${{alignc}}${{font Noto Sans:size=8}}${{color aaaaaa}}Carleton Place ${{color}}"
        f"${{color ffb454}}${{font Noto Sans:bold:size=11}}{temp}°C${{font}}${{color}}${{font Noto Sans:size=8}} "
        f"{desc}  ${{color aaaaaa}}Feels {feels}°  Hum {humidity}%${{color}}${{font}}"
    )
except Exception:
    print("${alignc}Weather unavailable")
