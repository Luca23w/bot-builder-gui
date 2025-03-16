import matplotlib
matplotlib.use("Agg")  # Verhindert GUI-Fehler, nutzt ein nicht-interaktives Backend
import matplotlib.pyplot as plt
import yfinance as yf
import pandas as pd
import io
import base64

from django.shortcuts import render
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image
from .forms import StockForm

def backtest_strategy(df, sma_period):
    """Einfache Strategie: Kaufen, wenn der Preis über dem SMA liegt; verkaufen, wenn er darunter liegt"""
    
    df["SMA"] = df["Close"].rolling(window=sma_period).mean()
    df["Signal"] = df["Close"] > df["SMA"]  # True = Buy, False = Sell
    df["Returns"] = df["Close"].pct_change()
    df["Strategy"] = df["Signal"].shift(1) * df["Returns"]
    df["Cumulative"] = (1 + df["Strategy"]).cumprod()

    # Performance berechnen (in %)
    performance = round((df["Cumulative"].iloc[-1] - 1) * 100, 2)
    
    # Anzahl der Trades berechnen
    df["Trades"] = df["Signal"].diff().abs()  # Zählt Umschaltungen (Buy/Sell)
    num_trades = int(df["Trades"].sum())

    return df, performance, num_trades

def stock_analysis(request):
    chart_url = None

    if request.method == "POST":
        form = StockForm(request.POST)
        if form.is_valid():
            ticker = form.cleaned_data["ticker"]
            sma_period = form.cleaned_data["sma_period"]

            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")

            if df.empty:
                return render(request, "analysis/index.html", {"form": form, "error": "Invalid ticker!"})

            df, performance, num_trades = backtest_strategy(df, sma_period)

            # Plot erstellen
            plt.figure(figsize=(10, 5))
            plt.plot(df.index, df["Close"], label="Close Price", color="blue")
            plt.plot(df.index, df["SMA"], label=f"SMA {sma_period}", color="red")
            plt.plot(df.index, df["Cumulative"] * df["Close"].iloc[0], label="Strategy Performance", color="green")
            plt.legend()
            plt.title(f"{ticker} - Stock Analysis & Strategy")

            buffer = io.BytesIO()
            plt.savefig(buffer, format="png")
            buffer.seek(0)
            chart_url = base64.b64encode(buffer.getvalue()).decode()
            buffer.close()
            plt.close()

            # Daten für das PDF in der Session speichern
            request.session["chart_url"] = chart_url
            request.session["performance"] = performance
            request.session["num_trades"] = num_trades
            request.session["date_range"] = f"{df.index.min().strftime('%Y-%m-%d')} bis {df.index.max().strftime('%Y-%m-%d')}"

    else:
        form = StockForm()

    return render(request, "analysis/index.html", {"form": form, "chart_url": chart_url})

def export_pdf(request):
    """Erstellt ein PDF mit der Matplotlib-Grafik und einer Tabelle zur Performance."""
    
    # Stelle sicher, dass die Grafik aus dem vorherigen Request verfügbar ist
    chart_url = request.session.get("chart_url")
    performance = request.session.get("performance", "N/A")
    num_trades = request.session.get("num_trades", "N/A")
    date_range = request.session.get("date_range", "N/A")

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="stock_analysis_report.pdf"'

    # ReportLab-Dokument erstellen
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    elements = []

    # Titel
    elements.append(canvas.Canvas(buffer, pagesize=letter).drawString(100, 750, "Stock Analysis Report"))

    # Tabelle mit Analyse-Daten
    data = [
        ["Zeitraum", "Performance (%)", "Anzahl Trades"],
        [date_range, f"{performance} %", num_trades]
    ]

    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.blue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)

    # Matplotlib-Grafik ins PDF einfügen
    if chart_url:
        image_data = base64.b64decode(chart_url)  # Base64 in Bild umwandeln
        image_io = io.BytesIO(image_data)
        img = Image(image_io, width=400, height=250)
        elements.append(img)

    # PDF speichern
    doc.build(elements)
    buffer.seek(0)
    response.write(buffer.read())
    buffer.close()

    return response
