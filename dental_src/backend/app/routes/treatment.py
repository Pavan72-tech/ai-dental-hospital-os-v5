from fastapi import APIRouter
router=APIRouter(prefix='/treatment',tags=['treatment'])
@router.get('/health')
def health(): return {'module':'treatment','status':'skeleton-ready'}
