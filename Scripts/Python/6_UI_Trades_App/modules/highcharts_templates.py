chart_render = """
<figure class="highcharts-figure">
    <div id="{container_name}"></div>
    <p class="highcharts-description">
        {chart_description}
    </p>
</figure>
"""

pie_chart_drilldown= """
Highcharts.chart('{container_name'}, {{
    chart: {{
        type: 'pie'
    }},
    title: {{
        text: {title_text},
        align: 'left'
    }},
    subtitle: {{
        text: {subtitle_text},
        align: 'left'
    }},
    accessibility: {{
        announceNewData: {{
            enabled: true
        }},
        point: {{
            valueSuffix: '%'
        }}
    }},
    plotOptions: {{
        series: {{
            dataLabels: {{
                enabled: true,
                format: '{{point.name}}: {{point.y:.1f}}%'
            }}
        }}
    }},
    tooltip: {{
        headerFormat: '<span style="font-size:11px">{series.name}</span><br>',
        pointFormat: '<span style="color:{point.color}">{point.name}</span>: <b>{point.y:.2f}%</b> of total<br/>'
    }},
    series: {series_type},
    {drilldown}
}})"""



def create_series_type():
    template_series = [
        {
            "name": 'Browsers',
            "colorByPoint": True,
            "data": []
        }
    ]
    template_series[0]["data"].append({"name": name, "y": data_point, "drilldown": drilldown_id})    
def create_drilldown():
    """
    drilldown: {{
        series: {drilldown_series}
    }}
    """