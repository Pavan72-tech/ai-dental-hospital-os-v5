from fastapi import APIRouter
router=APIRouter(prefix='/appointments',tags=['appointments'])
@router.get('/health')
def health(): return {'module':'appointments','status':'skeleton-ready'}
