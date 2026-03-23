#!/usr/bin/env bash

# Récupération des mises à jour en filtrant l'en‑tête \"Listing...\"
updates=$(apt list --upgradable 2>/dev/null | grep -v \"^Listing\")

if [ -z \"$updates\" ]; then
  payload='{\"type\":\"updates\",\"payload\":\"Aucune mise à jour disponible\"}'
else
  payload=$(jq -nc --arg p \"$updates\" '{\"type\":\"updates\",\"payload\":$p}')
fi

mosquitto_pub -h \"${MQTT_BROKER}\" -t \"${MQTT_REPLY_TOPIC}\" -m \"${payload}\"
