from fastapi import FastAPI
import uvicorn

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Настройка OpenTelemetry
resource = Resource(attributes={
    SERVICE_NAME: "service-a"
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


@app.get("/order")
def get_order():
    # дополнительный span для логики генерации заказа (опционально)
    with tracer.start_as_current_span("generate_order"):
        order = {"order_id": 123, "item": "Laptop", "price": 1500}
    return order
