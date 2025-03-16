from django import forms

class StockForm(forms.Form):
    ticker = forms.CharField(label="Stock Ticker", max_length=10)
    sma_period = forms.IntegerField(label="SMA Period", min_value=1, initial=20)
