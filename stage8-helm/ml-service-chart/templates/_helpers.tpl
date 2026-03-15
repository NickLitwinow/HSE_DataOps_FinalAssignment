{{/*
Полное имя ресурса
*/}}
{{- define "ml-service-chart.fullname" -}}
{{- printf "%s-ml-service" .Release.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Общие метки
*/}}
{{- define "ml-service-chart.labels" -}}
app: {{ include "ml-service-chart.fullname" . }}
chart: {{ .Chart.Name }}-{{ .Chart.Version }}
release: {{ .Release.Name }}
{{- end }}

{{/*
Метки для селектора
*/}}
{{- define "ml-service-chart.selectorLabels" -}}
app: {{ include "ml-service-chart.fullname" . }}
{{- end }}
