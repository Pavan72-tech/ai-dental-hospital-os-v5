from fastapi import APIRouter
router=APIRouter(prefix='/clinical',tags=['clinical'])
@router.get('/health')
def health(): return {'module':'clinical','status':'skeleton-ready'}
