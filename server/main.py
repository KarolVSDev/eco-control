from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.controller import auth_controller,eco_controller,dashboard_controller,history_controller,admin_controller
app=FastAPI(title='ECO CONTROL API',version='1.0.0')
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_list,allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
app.include_router(auth_controller.router,prefix='/api/v1')
app.include_router(eco_controller.router,prefix='/api/v1')
app.include_router(dashboard_controller.router,prefix='/api/v1')
app.include_router(history_controller.router,prefix='/api/v1')
app.include_router(admin_controller.router,prefix='/api/v1')
@app.get('/health')
def health(): return {'status':'ok'}
