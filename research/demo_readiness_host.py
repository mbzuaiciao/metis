"""Temporary loopback workstation host with a persistent three-attempt guard.

Serves the unchanged production build/API and saves private integration records.
Not application deployment code; close after the demo checks.
"""
import argparse
from datetime import datetime, timezone
import json
from itertools import count
from pathlib import Path
from time import monotonic

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.exceptions import ExceptionMiddleware
from starlette.responses import JSONResponse, Response
from starlette.staticfiles import StaticFiles

from metis.api.app import app as api_app
from observer_experiment import write_private

ROOT=Path(__file__).resolve().parents[1]
EXPECTED=['/api/reasoning','/api/reasoning','/api/causal-exploration']
INFERENCE=set(EXPECTED)


def create_host(directory):
    directory=Path(directory)
    manifest=json.loads((directory/'manifest.json').read_text())
    if manifest['attempts']!=8:raise ValueError('Complete the eight-attempt comparison first')
    static=StaticFiles(directory=ROOT/'frontend/dist',html=True)
    async def dispatch(scope,receive,send):
        target=api_app if scope['type']!='http' or scope['path'].startswith('/api/') else static
        await target(scope,receive,send)
    sequence=count(max([int(p.name.split('-')[1]) for p in directory.glob('ui-*-response.json')],default=0)+1)
    class Capture(BaseHTTPMiddleware):
        async def dispatch(self,request,call_next):
            if not request.url.path.startswith('/api/') or request.method!='POST':return await call_next(request)
            body=await request.json()
            if request.url.path in INFERENCE:
                attempts=len(list(directory.glob('integration-*-start.json')))
                if attempts>=3:
                    return JSONResponse({'detail':'Simulated inference failure (research guard; no Meta request). No demonstration fallback was used.'},status_code=502)
                if request.url.path!=EXPECTED[attempts]:
                    return JSONResponse({'detail':'Research guard: unexpected integration order; no Meta request.'},status_code=409)
                # The persistent intent is written before dispatch, including failed attempts.
                write_private(directory/f'integration-{attempts+1:02}-start.json',{'path':request.url.path,'body':body,'started_utc':datetime.now(timezone.utc).isoformat()})
            number=next(sequence)  # reserve before awaiting parallel calculations
            t=monotonic();response=await call_next(request)
            raw=b''.join([chunk async for chunk in response.body_iterator])
            write_private(directory/f'ui-{number:03}-response.json',{'path':request.url.path,'request':body,'status':response.status_code,'seconds':round(monotonic()-t,3),'body':json.loads(raw)})
            return Response(raw,status_code=response.status_code,headers=dict(response.headers),media_type=response.media_type)
    return Capture(ExceptionMiddleware(dispatch))


if __name__=='__main__':
    import uvicorn
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--records',type=Path,required=True)
    args=parser.parse_args()
    uvicorn.run(create_host(args.records),host='127.0.0.1',port=8002,access_log=False)
