"""Terminate an owned process using a handle bound to its creation identity."""
import os
import ctypes

def owned_tree(root):
    """Reject false child edges created when Windows reuses an exited parent PID."""
    import psutil
    result=[root];seen={root.pid};index=0
    while index<len(result):
        parent=result[index];index+=1
        try:
            parent_created=parent.create_time()
            for child in parent.children(recursive=False):
                if child.pid not in seen and child.create_time()>=parent_created:
                    seen.add(child.pid);result.append(child)
        except (psutil.NoSuchProcess,psutil.AccessDenied):pass
    return result

def stop_owned(pid,created):
    if os.name!='nt':
        import psutil
        try:
            p=psutil.Process(pid)
            if p.create_time()!=created:return False
            p.terminate();return True
        except psutil.Error:return False
    from ctypes import wintypes
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.GetProcessTimes.argtypes=[wintypes.HANDLE,*([ctypes.POINTER(wintypes.FILETIME)]*4)]
    kernel.TerminateProcess.argtypes=[wintypes.HANDLE,wintypes.UINT];kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=kernel.OpenProcess(0x1001,False,pid)
    if not handle:return False
    try:
        stamps=[wintypes.FILETIME() for _ in range(4)]
        if not kernel.GetProcessTimes(handle,*[ctypes.byref(x) for x in stamps]):return False
        ticks=(stamps[0].dwHighDateTime<<32)|stamps[0].dwLowDateTime
        actual=ticks/10_000_000-11644473600
        if abs(actual-created)>0.00001:return False
        return bool(kernel.TerminateProcess(handle,137))
    finally:kernel.CloseHandle(handle)
