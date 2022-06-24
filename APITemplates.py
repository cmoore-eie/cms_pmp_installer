def uses_values_list() -> list:
    uses_values = list()
    uses_values.append("uses gw.pmp.scheme.util.SchemeUtil_PMP\n")
    uses_values.append("uses gw.pmp.annotations.ApiOverride_PMP\n")
    uses_values.append("uses gw.rest.core.pc.policyperiod.v1.coverage.ClauseWrapper\n")
    uses_values.append("uses java.util.stream.Stream\n")
    uses_values.append("\n")
    return uses_values


def load_values_list() -> list:
    load_values = list()
    load_values.append('\n')
    load_values.append('  @ApiOverride_PMP(:name="loadValues")\n')
    load_values.append('  protected override function loadValues() : Stream {\n')
    load_values.append('    var retVal = super.loadValues()\n')
    load_values.append('    for(item in retVal.toArray()){\n')
    load_values.append('      if(item typeis ClauseWrapper) {\n')
    load_values.append('        SchemeUtil_PMP.isCoverageIncluded(item.Pattern.CodeIdentifier, true, Coverable)\n')
    load_values.append('      }\n')
    load_values.append('    }\n')
    load_values.append('    return retVal\n')
    load_values.append('  }\n')
    return load_values
