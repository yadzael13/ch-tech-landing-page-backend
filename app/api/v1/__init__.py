from fastapi import APIRouter

from app.api.v1.articles import admin_router as articles_admin_router
from app.api.v1.articles import public_router as articles_public_router
from app.api.v1.auth import router as auth_router
from app.api.v1.case_studies import admin_router as case_studies_admin_router
from app.api.v1.case_studies import public_router as case_studies_public_router
from app.api.v1.clients import admin_router as clients_admin_router
from app.api.v1.clients import public_router as clients_public_router
from app.api.v1.company import admin_router as company_admin_router
from app.api.v1.company import public_router as company_public_router
from app.api.v1.contact import router as contact_router
from app.api.v1.partners import admin_router as partners_admin_router
from app.api.v1.partners import public_router as partners_public_router
from app.api.v1.products import admin_router as products_admin_router
from app.api.v1.products import public_router as products_public_router
from app.api.v1.projects import admin_router as projects_admin_router
from app.api.v1.projects import public_router as projects_public_router
from app.api.v1.service_lines import admin_router as service_lines_admin_router
from app.api.v1.service_lines import public_router as service_lines_public_router
from app.api.v1.services import admin_router as services_admin_router
from app.api.v1.services import public_router as services_public_router
from app.api.v1.team_members import admin_router as team_members_admin_router
from app.api.v1.team_members import public_router as team_members_public_router
from app.api.v1.technologies import admin_router as technologies_admin_router
from app.api.v1.technologies import public_router as technologies_public_router
from app.api.v1.testimonials import admin_router as testimonials_admin_router
from app.api.v1.testimonials import public_router as testimonials_public_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(projects_public_router)
api_router.include_router(projects_admin_router)
api_router.include_router(technologies_public_router)
api_router.include_router(technologies_admin_router)
api_router.include_router(services_public_router)
api_router.include_router(services_admin_router)
api_router.include_router(articles_public_router)
api_router.include_router(articles_admin_router)
api_router.include_router(case_studies_public_router)
api_router.include_router(case_studies_admin_router)
api_router.include_router(contact_router)
api_router.include_router(company_public_router)
api_router.include_router(company_admin_router)
api_router.include_router(service_lines_public_router)
api_router.include_router(service_lines_admin_router)
api_router.include_router(clients_public_router)
api_router.include_router(clients_admin_router)
api_router.include_router(partners_public_router)
api_router.include_router(partners_admin_router)
api_router.include_router(testimonials_public_router)
api_router.include_router(testimonials_admin_router)
api_router.include_router(products_public_router)
api_router.include_router(products_admin_router)
api_router.include_router(team_members_public_router)
api_router.include_router(team_members_admin_router)
