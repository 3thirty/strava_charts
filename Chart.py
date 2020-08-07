from pychartjs import BaseChart, ChartType, Color, Options


class Chart(BaseChart):
    type = ChartType.Line

    class labels:
        labels = []

    class data:
        class Power:
            data = []
            _color = Color.JSLinearGradient('ctx', 0, 0, 1000, 0)
            _color.addColorStop(0, Color.Green)

            borderColor = _color.returnGradient()
            fill = False
            pointBorderWidth = 10
            pointRadius = 3
            spanGaps = True
            lineTension = 0.2

    class options:
        title = Options.Title(text="Power over time", fontSize=18)

        _labels = Options.Legend_Labels(fontColor=Color.Gray, fullWidth=True)
        legend = Options.Legend(position='Bottom', labels=_labels)

        _yAxes = [
            Options.General(
                ticks=Options.General(
                    beginAtZero=True,
                    padding=15,
                    max=200
                ),
            )
        ]

        scales = Options.General(
            yAxes=_yAxes,
            responsive=True
        )
