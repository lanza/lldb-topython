# lldb-topython

#### Examples

```
(lldb) topython po
Help on method EvaluateExpression in lldb.SBFrame:

lldb.SBFrame.EvaluateExpression = EvaluateExpression(self, *args) unbound lldb.SBFrame method
    EvaluateExpression(self, str expr) -> SBValue
    EvaluateExpression(self, str expr, DynamicValueType use_dynamic) -> SBValue
    EvaluateExpression(self, str expr, DynamicValueType use_dynamic, bool unwind_on_error) -> SBValue
    EvaluateExpression(self, str expr, SBExpressionOptions options) -> SBValue
    
    The version that doesn't supply a 'use_dynamic' value will use the
    target's default.
```

```
(lldb) topython break mod -i 0 --enable
Help on method SetIgnoreCount in lldb.SBBreakpoint:

lldb.SBBreakpoint.SetIgnoreCount = SetIgnoreCount(self, *args) unbound lldb.SBBreakpoint method
    SetIgnoreCount(self, uint32_t count)

Help on method SetEnabled in lldb.SBBreakpoint:

lldb.SBBreakpoint.SetEnabled = SetEnabled(self, *args) unbound lldb.SBBreakpoint method
    SetEnabled(self, bool enable)

lldb.SBBreakpoint.SetEnabled(True)
```

```
(lldb) topython thread jump
Help on method JumpToLine in lldb.SBThread:

lldb.SBThread.JumpToLine = JumpToLine(self, *args) unbound lldb.SBThread method
    JumpToLine(self, SBFileSpec file_spec, uint32_t line) -> SBError
```
