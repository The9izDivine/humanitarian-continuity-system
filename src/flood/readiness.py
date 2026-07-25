"""Evidence-aware flood evacuation readiness engine."""

from __future__ import annotations

from datetime import datetime

from src.flood.models import (
    EvacuationOrder,
    FloodIncident,
    FloodResponsePlan,
    FloodZone,
    Household,
    RouteStatus,
    ShelterAssignment,
    TransportationAsset,
)
from src.flood.readiness_models import (
    FloodReadinessCondition,
    FloodReadinessResult,
)
from src.flood.world import SyntheticFloodWorld


POLICY_ID = "HCS-POL-FLOOD-READINESS-001"
POLICY_VERSION = "1.0.0"


class FloodReadinessEvaluationError(ValueError):
    """Raised when flood readiness cannot be evaluated safely."""


class FloodReadinessEngine:
    """Evaluate current evacuation readiness for a flood-response plan."""

    def evaluate(
        self,
        *,
        world: SyntheticFloodWorld,
        plan_id: str,
        household_id: str,
        evaluated_at: str,
    ) -> FloodReadinessResult:
        """Evaluate one plan and household at one point in time."""

        evaluation_time = self._parse_timestamp(evaluated_at)

        plan = self._require_type(
            world,
            plan_id,
            FloodResponsePlan,
        )
        incident = self._require_type(
            world,
            plan.incident_id,
            FloodIncident,
        )
        household = self._require_type(
            world,
            household_id,
            Household,
        )

        if household.zone_id not in plan.zone_ids:
            raise FloodReadinessEvaluationError(
                f"Household {household.object_id} belongs to zone "
                f"{household.zone_id}, which is outside plan {plan_id}."
            )

        zone = self._require_type(
            world,
            household.zone_id,
            FloodZone,
        )

        orders = tuple(
            self._require_type(world, object_id, EvacuationOrder)
            for object_id in plan.evacuation_order_ids
            if self._require_type(
                world,
                object_id,
                EvacuationOrder,
            ).zone_id == zone.object_id
        )

        routes = tuple(
            self._require_type(world, object_id, RouteStatus)
            for object_id in plan.route_ids
            if self._require_type(
                world,
                object_id,
                RouteStatus,
            ).zone_id == zone.object_id
        )

        assets = tuple(
            self._require_type(
                world,
                object_id,
                TransportationAsset,
            )
            for object_id in plan.transportation_asset_ids
        )

        assignments = tuple(
            self._require_type(
                world,
                object_id,
                ShelterAssignment,
            )
            for object_id in plan.shelter_assignment_ids
            if self._require_type(
                world,
                object_id,
                ShelterAssignment,
            ).household_id == household.object_id
        )

        conditions = (
            self._condition(
                "INCIDENT_VERIFIED",
                incident.verification_status == "VERIFIED",
                incident.evidence_ids,
                (
                    "Flood incident verification status is "
                    f"{incident.verification_status!r}."
                ),
            ),
            self._condition(
                "NO_MATERIAL_CHANGE",
                not incident.material_change_detected,
                incident.evidence_ids,
                (
                    "Material change detected is "
                    f"{incident.material_change_detected!r}."
                ),
            ),
            self._condition(
                "ZONE_REQUIRES_EVACUATION",
                zone.evacuation_required,
                zone.evidence_ids,
                (
                    "Zone evacuation requirement is "
                    f"{zone.evacuation_required!r}."
                ),
            ),
            self._evaluate_order(
                orders=orders,
                evaluated_at=evaluation_time,
            ),
            self._evaluate_plan_authority(
                plan=plan,
                evaluated_at=evaluation_time,
            ),
            self._condition(
                "PLAN_NOT_SUPERSEDED",
                (
                    plan.superseded_by is None
                    and plan.plan_status != "SUPERSEDED"
                ),
                plan.evidence_ids,
                (
                    f"Plan status is {plan.plan_status!r}; "
                    f"superseded_by={plan.superseded_by!r}."
                ),
            ),
            self._evaluate_route(
                routes=routes,
                household=household,
            ),
            self._evaluate_transport(
                assets=assets,
                household=household,
                plan_id=plan.object_id,
            ),
            self._evaluate_shelter_assignment(
                assignments=assignments,
                household=household,
            ),
        )

        failed = tuple(
            item.condition_id
            for item in conditions
            if item.satisfied is False
        )
        unknown = tuple(
            item.condition_id
            for item in conditions
            if item.satisfied is None
        )
        evidence_ids = tuple(
            evidence_id
            for item in conditions
            for evidence_id in item.evidence_ids
        )

        if failed:
            outcome = "BLOCKED"
        elif unknown:
            outcome = "INSUFFICIENT_EVIDENCE"
        else:
            outcome = "READY_FOR_EVACUATION"

        if failed:
            explanation = (
                f"Flood plan {plan.object_id} is BLOCKED; "
                f"failed conditions: {', '.join(failed)}."
            )
        elif unknown:
            explanation = (
                f"Flood plan {plan.object_id} has "
                "INSUFFICIENT_EVIDENCE; unknown conditions: "
                f"{', '.join(unknown)}."
            )
        else:
            explanation = (
                f"Flood plan {plan.object_id} is "
                "READY_FOR_EVACUATION; all mandatory readiness "
                "conditions are satisfied."
            )

        return FloodReadinessResult(
            plan_id=plan.object_id,
            incident_id=incident.object_id,
            outcome=outcome,
            policy_id=POLICY_ID,
            policy_version=POLICY_VERSION,
            evaluated_at=evaluated_at,
            conditions=conditions,
            failed_conditions=failed,
            unknown_conditions=unknown,
            evidence_ids=evidence_ids,
            explanation=explanation,
        )

    @staticmethod
    def _condition(
        condition_id: str,
        satisfied: bool | None,
        evidence_ids: tuple[str, ...],
        explanation: str,
    ) -> FloodReadinessCondition:
        return FloodReadinessCondition(
            condition_id=condition_id,
            satisfied=satisfied,
            evidence_ids=evidence_ids,
            explanation=explanation,
        )

    def _evaluate_order(
        self,
        *,
        orders: tuple[EvacuationOrder, ...],
        evaluated_at: datetime,
    ) -> FloodReadinessCondition:
        if not orders:
            return self._condition(
                "EVACUATION_ORDER_CURRENT",
                None,
                (),
                "No evacuation order exists for the governed zone.",
            )

        current_orders = tuple(
            order
            for order in orders
            if (
                order.order_status == "ACTIVE"
                and order.superseded_by is None
            )
        )

        if not current_orders:
            return self._condition(
                "EVACUATION_ORDER_CURRENT",
                False,
                tuple(
                    evidence_id
                    for order in orders
                    for evidence_id in order.evidence_ids
                ),
                "No active, non-superseded evacuation order exists.",
            )

        order = current_orders[0]

        if order.valid_until is None:
            return self._condition(
                "EVACUATION_ORDER_CURRENT",
                None,
                order.evidence_ids,
                "Evacuation order has no validity endpoint.",
            )

        valid_until = self._parse_timestamp(order.valid_until)
        satisfied = evaluated_at <= valid_until

        return self._condition(
            "EVACUATION_ORDER_CURRENT",
            satisfied,
            order.evidence_ids,
            (
                f"Evacuation order {order.object_id} is valid until "
                f"{order.valid_until}."
            ),
        )

    def _evaluate_plan_authority(
        self,
        *,
        plan: FloodResponsePlan,
        evaluated_at: datetime,
    ) -> FloodReadinessCondition:
        if plan.authority_valid_until is None:
            return self._condition(
                "PLAN_AUTHORITY_CURRENT",
                None,
                plan.evidence_ids,
                "Plan authority validity endpoint is missing.",
            )

        valid_until = self._parse_timestamp(
            plan.authority_valid_until
        )

        return self._condition(
            "PLAN_AUTHORITY_CURRENT",
            evaluated_at <= valid_until,
            plan.evidence_ids,
            (
                f"Plan authority is valid until "
                f"{plan.authority_valid_until}."
            ),
        )

    def _evaluate_route(
        self,
        *,
        routes: tuple[RouteStatus, ...],
        household: Household,
    ) -> FloodReadinessCondition:
        if not routes:
            return self._condition(
                "ROUTE_AVAILABLE",
                None,
                (),
                "No route evidence exists for the household zone.",
            )

        viable = tuple(
            route
            for route in routes
            if (
                route.viability_status == "OPEN"
                and route.capacity_per_hour > 0
            )
        )

        if not viable:
            return self._condition(
                "ROUTE_AVAILABLE",
                False,
                tuple(
                    evidence_id
                    for route in routes
                    for evidence_id in route.evidence_ids
                ),
                "No open route with positive capacity exists.",
            )

        if (
            household.mobility_support_required
            and not any(
                route.accessible_transport_supported
                for route in viable
            )
        ):
            return self._condition(
                "ROUTE_AVAILABLE",
                False,
                tuple(
                    evidence_id
                    for route in viable
                    for evidence_id in route.evidence_ids
                ),
                "No viable route supports accessible transport.",
            )

        return self._condition(
            "ROUTE_AVAILABLE",
            True,
            tuple(
                evidence_id
                for route in viable
                for evidence_id in route.evidence_ids
            ),
            "At least one viable route satisfies household needs.",
        )

    def _evaluate_transport(
        self,
        *,
        assets: tuple[TransportationAsset, ...],
        household: Household,
        plan_id: str,
    ) -> FloodReadinessCondition:
        if not household.transport_required:
            return self._condition(
                "TRANSPORT_READY",
                True,
                (),
                "Household does not require managed transport.",
            )

        if not assets:
            return self._condition(
                "TRANSPORT_READY",
                None,
                (),
                "No transportation assets are registered.",
            )

        ready_assets = tuple(
            asset
            for asset in assets
            if (
                asset.readiness_status == "READY"
                and asset.assigned_plan_id in {None, plan_id}
                and asset.capacity >= household.household_size
            )
        )

        if not ready_assets:
            return self._condition(
                "TRANSPORT_READY",
                False,
                tuple(
                    evidence_id
                    for asset in assets
                    for evidence_id in asset.evidence_ids
                ),
                "No ready transportation asset has sufficient capacity.",
            )

        if (
            household.mobility_support_required
            and not any(
                asset.accessible_capacity >= 1
                for asset in ready_assets
            )
        ):
            return self._condition(
                "TRANSPORT_READY",
                False,
                tuple(
                    evidence_id
                    for asset in ready_assets
                    for evidence_id in asset.evidence_ids
                ),
                "No ready asset has accessible capacity.",
            )

        return self._condition(
            "TRANSPORT_READY",
            True,
            tuple(
                evidence_id
                for asset in ready_assets
                for evidence_id in asset.evidence_ids
            ),
            "A ready transportation asset satisfies capacity needs.",
        )

    def _evaluate_shelter_assignment(
        self,
        *,
        assignments: tuple[ShelterAssignment, ...],
        household: Household,
    ) -> FloodReadinessCondition:
        if not assignments:
            return self._condition(
                "SHELTER_ASSIGNMENT_READY",
                None,
                (),
                "No shelter assignment exists for the household.",
            )

        valid_assignments = tuple(
            assignment
            for assignment in assignments
            if (
                assignment.assignment_status
                in {"RESERVED", "CONFIRMED"}
                and assignment.intake_authority_status == "VALID"
            )
        )

        if not valid_assignments:
            return self._condition(
                "SHELTER_ASSIGNMENT_READY",
                False,
                tuple(
                    evidence_id
                    for assignment in assignments
                    for evidence_id in assignment.evidence_ids
                ),
                "No governed shelter assignment is currently valid.",
            )

        if (
            household.mobility_support_required
            and not any(
                assignment.accessible_space_required
                for assignment in valid_assignments
            )
        ):
            return self._condition(
                "SHELTER_ASSIGNMENT_READY",
                False,
                tuple(
                    evidence_id
                    for assignment in valid_assignments
                    for evidence_id in assignment.evidence_ids
                ),
                "Shelter assignment does not preserve accessibility.",
            )

        return self._condition(
            "SHELTER_ASSIGNMENT_READY",
            True,
            tuple(
                evidence_id
                for assignment in valid_assignments
                for evidence_id in assignment.evidence_ids
            ),
            "A valid shelter assignment satisfies household needs.",
        )

    @staticmethod
    def _require_type(
        world: SyntheticFloodWorld,
        object_id: str,
        expected_type: type,
    ):
        item = world.get_object(object_id)

        if not isinstance(item, expected_type):
            raise FloodReadinessEvaluationError(
                f"{object_id} is {type(item).__name__}; "
                f"expected {expected_type.__name__}."
            )

        return item

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise FloodReadinessEvaluationError(
                f"Invalid timestamp: {value}"
            ) from exc