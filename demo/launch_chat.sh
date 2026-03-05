#!/bin/bash
# Script para lanzar la UI de chat

export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

cd /Users/javiersculli/dev/caf

echo "🚀 Lanzando Analista IA - Chat UI..."
echo ""
echo "   La interfaz se abrirá automáticamente en tu browser"
echo "   URL: http://localhost:8501"
echo ""
echo "   Presiona Ctrl+C para detener"
echo ""

python3 -m streamlit run demo/ui/chat_app.py
