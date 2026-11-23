from datetime import timedelta

from rest_framework import serializers

from apps.espacios.models import Espacio
from apps.operaciones.models import Pago
from apps.vehiculos.serializers import normalizar_placa

from .models import Mensualidad, PlanMensual
from .reglas import hoy


class PlanMensualSerializer(serializers.ModelSerializer):
    tipo_vehiculo_nombre = serializers.CharField(source="tipo_vehiculo.nombre", read_only=True)

    class Meta:
        model = PlanMensual
        fields = ["id", "nombre", "tipo_vehiculo", "tipo_vehiculo_nombre", "valor", "dias", "activo"]

    def validate_valor(self, valor):
        if valor <= 0:
            raise serializers.ValidationError("El valor debe ser mayor que cero.")
        return valor

    def validate_dias(self, dias):
        if dias < 1:
            raise serializers.ValidationError("El plan debe durar al menos un día.")
        return dias


class MensualidadSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True)
    cliente_documento = serializers.CharField(source="cliente.documento", read_only=True)
    cliente_telefono = serializers.CharField(source="cliente.telefono", read_only=True)
    placa = serializers.CharField(source="vehiculo.placa", read_only=True)
    tipo_vehiculo = serializers.CharField(source="vehiculo.tipo_vehiculo.nombre", read_only=True)
    plan_nombre = serializers.CharField(source="plan.nombre", read_only=True)
    espacio_fijo_codigo = serializers.CharField(source="espacio_fijo.codigo", read_only=True, default=None)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    valor_pagado = serializers.SerializerMethodField()
    dias_restantes = serializers.SerializerMethodField()

    class Meta:
        model = Mensualidad
        fields = [
            "id", "cliente", "cliente_nombre", "cliente_documento", "cliente_telefono", "vehiculo", "placa",
            "tipo_vehiculo", "plan", "plan_nombre", "espacio_fijo", "espacio_fijo_codigo",
            "fecha_inicio", "fecha_fin", "estado", "estado_display", "valor_pagado", "dias_restantes",
        ]

    def get_valor_pagado(self, mensualidad):
        return sum(int(p.valor) for p in mensualidad.pagos.all())

    def get_dias_restantes(self, mensualidad):
        """Días que le quedan contando hoy (0 si ya venció)."""
        if mensualidad.estado != Mensualidad.Estado.VIGENTE:
            return 0
        desde = max(hoy(), mensualidad.fecha_inicio)
        return max(0, (mensualidad.fecha_fin - desde).days + 1)


class VentaSerializer(serializers.Serializer):
    """
    POST /api/mensualidades/
    {documento, nombre, telefono?, correo?, placa, plan, espacio_fijo?, fecha_inicio?, metodo}

    El cliente se busca por documento (se crea si no existe) y el vehículo por placa
    (se crea con el tipo del plan si no existe).
    """

    documento = serializers.CharField(max_length=20)
    nombre = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    telefono = serializers.CharField(max_length=30, required=False, allow_blank=True, default="")
    correo = serializers.EmailField(required=False, allow_blank=True, default="")
    placa = serializers.CharField(max_length=10)
    plan = serializers.PrimaryKeyRelatedField(queryset=PlanMensual.objects.filter(activo=True).select_related("tipo_vehiculo"))
    espacio_fijo = serializers.PrimaryKeyRelatedField(
        queryset=Espacio.objects.select_related("zona"), required=False, allow_null=True
    )
    fecha_inicio = serializers.DateField(required=False)
    metodo = serializers.ChoiceField(choices=Pago.Metodo.choices)

    def validate_placa(self, valor):
        return normalizar_placa(valor)

    def validate_fecha_inicio(self, fecha):
        if fecha < hoy():
            raise serializers.ValidationError("La mensualidad no puede empezar en una fecha pasada.")
        return fecha

    def validate(self, attrs):
        from apps.vehiculos.models import Cliente, Vehiculo

        attrs.setdefault("fecha_inicio", hoy())
        plan = attrs["plan"]

        if not Cliente.objects.filter(documento=attrs["documento"].strip()).exists() and not attrs["nombre"].strip():
            raise serializers.ValidationError({"nombre": "Es un cliente nuevo: escribe su nombre."})

        vehiculo = Vehiculo.objects.filter(placa=attrs["placa"]).first()
        if vehiculo is not None:
            if vehiculo.tipo_vehiculo_id != plan.tipo_vehiculo_id:
                raise serializers.ValidationError(
                    {"plan": f"El vehículo {vehiculo.placa} es {vehiculo.tipo_vehiculo} y el plan es para {plan.tipo_vehiculo}."}
                )
            fin = attrs["fecha_inicio"] + timedelta(days=plan.dias - 1)
            choca = vehiculo.mensualidades.filter(
                estado=Mensualidad.Estado.VIGENTE, fecha_inicio__lte=fin, fecha_fin__gte=attrs["fecha_inicio"]
            ).first()
            if choca:
                raise serializers.ValidationError(
                    {"placa": f"{vehiculo.placa} ya tiene una mensualidad hasta el {choca.fecha_fin:%d/%m/%Y}. Usa Renovar."}
                )

        espacio = attrs.get("espacio_fijo")
        if espacio is not None:
            if espacio.zona.tipo_vehiculo_id != plan.tipo_vehiculo_id:
                raise serializers.ValidationError({"espacio_fijo": f"El espacio {espacio.codigo} no es para {plan.tipo_vehiculo}."})
            if espacio.estado == Espacio.Estado.INACTIVO:
                raise serializers.ValidationError({"espacio_fijo": f"El espacio {espacio.codigo} está inactivo."})
            otra = espacio.mensualidades.filter(estado=Mensualidad.Estado.VIGENTE).exclude(vehiculo=vehiculo).first()
            if otra:
                raise serializers.ValidationError(
                    {"espacio_fijo": f"El espacio {espacio.codigo} ya es el fijo de {otra.vehiculo.placa}."}
                )
        return attrs


class RenovacionSerializer(serializers.Serializer):
    """POST /api/mensualidades/{id}/renovar/ {metodo, plan?}"""

    metodo = serializers.ChoiceField(choices=Pago.Metodo.choices)
    plan = serializers.PrimaryKeyRelatedField(queryset=PlanMensual.objects.filter(activo=True), required=False)
