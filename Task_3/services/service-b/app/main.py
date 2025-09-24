from fastapi import FastAPI
import uvicorn
import requests

# OpenTelemetry
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Настройка OpenTelemetry
resource = Resource(attributes={
    SERVICE_NAME: "serviceb"
})

jaeger_exporter = JaegerExporter( #jaeger
   agent_host_name="jaeger",
   agent_port=6831,
)

provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(jaeger_exporter)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Инструментируем
app = FastAPI()
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()

tracer = trace.get_tracer(__name__)

provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))


@app.get("/calc")
def calc_with_order():
    with tracer.start_as_current_span("pay") as span:
        # вызываем order-service
        response = requests.get("http://service-a:8080/order")
        order = response.json()
        
        # можно добавить атрибуты span для лучшей трассировки
        span.set_attribute("order.id", order["order_id"])
        span.set_attribute("order.item", order["item"])
        span.set_attribute("order.price", order["price"])
        
        total = order["price"] * 1.2  # например, добавляем НДС
        
    return {"order": order, "total_with_tax": total}
