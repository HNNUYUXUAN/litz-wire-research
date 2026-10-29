"""Launch the fixed upstream server with explicit Student-edition compatibility.

The pinned MCP connector omits Desktop.student_version. This project-local
launcher passes it when LITZ_AEDT_EDITION=student; upstream source is unchanged.
"""
import os
from functools import wraps
from ansys.aedt.core import Desktop

if os.environ.get('LITZ_AEDT_EDITION')=='student':
    original=Desktop.__init__
    @wraps(original)
    def student_init(self,*args,**kwargs):
        import inspect
        bound=inspect.signature(original).bind_partial(self,*args,**kwargs)
        if 'student_version' not in bound.arguments:kwargs['student_version']=True
        return original(self,*args,**kwargs)
    Desktop.__init__=student_init

from ansys.aedt.mcp.__main__ import launcher
if __name__=='__main__':launcher()
