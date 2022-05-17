import requests

def get_alerts() -> dict:
    r = requests.get("https://api.alerts.in.ua/v2/alerts/active.json")
    alerts = r.json() # {'alerts': [{'u': 1649405066, 's': 1649090739, 'n': 'Луганська', 't': 'o'}], 'meta': {'last_updated_at': '2022/05/07 18:46:28 +0000', 'type': 'compact'}, 'contact': 'api@alerts.in.ua'}
    alerts_updated = alerts["meta"]["last_updated_at"].split()

    return {"alerts": [alert["n"] for alert in alerts["alerts"]], "updated_at": f"{alerts_updated[0]} {alerts_updated[1]}"}

print(get_alerts())