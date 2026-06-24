"""
Simulation endpoints for event and failure analysis.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any, List
import logging

from api.models import (
    EventSimulationRequest,
    FailureSimulationRequest,
    ExhaustiveSimulationRequest,
    ReportRequest,
    EventSimulationResponse,
    FailureSimulationResponse,
    ExhaustiveSimulationResponse,
    SimulationReportResponse
)
from api.dependencies import get_client
from saag import Client
from saag.usecases import SimulationMode
from saag.core.layers import AnalysisLayer
from api.presenters import simulation_presenter
from api._cancellable_runner import run_with_disconnect_watch, ClientDisconnected

router = APIRouter(prefix="/api/v1/simulation", tags=["simulation"])
logger = logging.getLogger(__name__)


@router.post("/event", response_model=EventSimulationResponse)
async def simulate_event(
    request: EventSimulationRequest,
    raw_request: Request,
    client: Client = Depends(get_client)
):
    """
    Run event simulation from a source application.
    """
    try:
        logger.info(f"Running event simulation: source={request.source_app}, messages={request.num_messages}")
        result = await run_with_disconnect_watch(
            raw_request,
            lambda ce: client.simulate(
                mode="event",
                layer="system",
                source_app=request.source_app,
                num_messages=request.num_messages,
                duration=request.duration
            ),
        )
        return simulation_presenter.format_event_simulation_response(result)
    except ClientDisconnected:
        raise HTTPException(status_code=499, detail="Client disconnected; operation stopped")
    except Exception as e:
        logger.error(f"Event simulation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Event simulation failed: {str(e)}")


@router.post("/failure", response_model=FailureSimulationResponse)
async def simulate_failure(
    request: FailureSimulationRequest,
    raw_request: Request,
    client: Client = Depends(get_client)
):
    """
    Run failure simulation for a target component.
    """
    try:
        layer_enum = AnalysisLayer.from_string(request.layer)
        layer_canonical = layer_enum.value
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    try:
        logger.info(f"Running composite failure simulation: targets={request.target_ids}, layer={layer_canonical}")
        result = await run_with_disconnect_watch(
            raw_request,
            lambda ce: client.simulate(
                target_ids=request.target_ids,
                layer=layer_canonical,
                mode="single"
            ),
        )
        return simulation_presenter.format_failure_simulation_response([result])
    except ClientDisconnected:
        raise HTTPException(status_code=499, detail="Client disconnected; operation stopped")
    except Exception as e:
        logger.error(f"Failure simulation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failure simulation failed: {str(e)}")


@router.post("/exhaustive", response_model=ExhaustiveSimulationResponse)
async def simulate_exhaustive(
    request: ExhaustiveSimulationRequest,
    raw_request: Request,
    client: Client = Depends(get_client)
):
    """
    Run exhaustive failure analysis for all components in a layer.
    """
    try:
        layer_enum = AnalysisLayer.from_string(request.layer)
        layer_canonical = layer_enum.value
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    try:
        logger.info(f"Running exhaustive failure analysis: layer={layer_canonical}")
        results = await run_with_disconnect_watch(
            raw_request,
            lambda ce: client.simulate(layer=layer_canonical, mode="exhaustive"),
        )
        return simulation_presenter.format_exhaustive_simulation_response(results, layer_canonical)
    except ClientDisconnected:
        raise HTTPException(status_code=499, detail="Client disconnected; operation stopped")
    except Exception as e:
        logger.error(f"Exhaustive simulation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Exhaustive simulation failed: {str(e)}")


@router.post("/report", response_model=SimulationReportResponse)
async def generate_simulation_report(
    request: ReportRequest,
    raw_request: Request,
    client: Client = Depends(get_client)
):
    """
    Generate comprehensive simulation report with analysis across multiple layers.
    """
    mapped_layers = []
    for layer in request.layers:
        try:
            layer_enum = AnalysisLayer.from_string(layer)
            mapped_layers.append(layer_enum.value)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )

    try:
        logger.info(f"Generating simulation report: layers={mapped_layers}")
        report = await run_with_disconnect_watch(
            raw_request,
            lambda ce: client.simulate(layer="system", mode="report", layers=mapped_layers),
        )
        return simulation_presenter.format_simulation_report_response(report)
    except ClientDisconnected:
        raise HTTPException(status_code=499, detail="Client disconnected; operation stopped")
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")



