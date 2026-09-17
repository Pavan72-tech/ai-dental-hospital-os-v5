from fastapi import APIRouter
router=APIRouter(prefix='/analytics',tags=['analytics'])
@router.get('/health')
def health(): return {'module':'analytics','status':'skeleton-ready'}
