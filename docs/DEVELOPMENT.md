# Development Guide

## Getting Started

### Prerequisites

- **Python**: 3.8 or higher
- **pip**: Package installer for Python
- **Modern browser**: Chrome, Firefox, Safari, or Edge

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd house-in-engelberg
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development tools
   ```

3. **Verify installation**:
   ```bash
   python scripts/validate_system.py
   # Should show: all checks passing (currently 403/403)
   ```

4. **Generate data**:
   ```bash
   python scripts/generate_all_data.py
   ```

5. **Run tests**:
   ```bash
   python -m pytest tests/ -v
   # Should show: all tests passing (currently 154 passed)
   ```

## Development Workflow

### Making Changes

1. **Modify code** in `engelberg/` package
2. **Add/update tests** in `tests/`
3. **Run tests** to verify: `python -m pytest tests/ -v`
4. **Regenerate data**: `python scripts/generate_all_data.py`
5. **Validate system**: `python scripts/validate_system.py`
6. **Test in browser**: Start server and manually test UI

### Testing Strategy

#### Unit Tests

**Location**: `tests/unit/`

**Purpose**: Test individual functions in isolation

**Example**:
```python
def test_annual_cash_flows_calculation():
    """Test that compute_annual_cash_flows produces expected results."""
    config = create_test_config()
    result = compute_annual_cash_flows(config)

    assert result['noi'] > 0
    assert result['cash_flow_per_owner'] < result['noi']
    assert 'tax_savings_per_owner' in result
```

**Run**:
```bash
python -m pytest tests/unit/ -v
```

#### Integration Tests

**Location**: `tests/integration/`

**Purpose**: Test complete workflows end-to-end

**Example**:
```python
def test_base_case_analysis_workflow():
    """Test full base case analysis workflow."""
    json_path = 'assumptions/assumptions.json'
    result = run_base_case_analysis(json_path)

    assert 'annual_results' in result
    assert 'irr_results' in result
    assert 'projection' in result
```

**Run**:
```bash
python -m pytest tests/integration/ -v
```

#### Regression Tests

**Location**: `tests/regression/`

**Purpose**: Verify calculations don't drift from known-good values

**Run**:
```bash
python -m pytest tests/regression/ -v
```

### Code Quality

#### Running All Tests

```bash
# All tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=engelberg --cov-report=html

# Fast (skip slow tests)
python -m pytest tests/ -v -m "not slow"

# Specific test file
python -m pytest tests/unit/test_core_calculations.py -v
```

#### Code Style

**Recommended tools** (install with `pip install -r requirements-dev.txt`):

```bash
# Format code
black engelberg/ scripts/ tests/

# Check style
flake8 engelberg/ scripts/ tests/ --extend-ignore=E501,W503,E203

# Type checking
mypy engelberg/ --ignore-missing-imports
```

#### Pre-Commit Checklist

- [ ] All tests pass: `python -m pytest tests/`
- [ ] No linter errors: `flake8 engelberg/`
- [ ] System validation passes: `python scripts/validate_system.py`
- [ ] Data regenerated if calculations changed: `python scripts/generate_all_data.py`
- [ ] Browser testing completed (test key scenarios and horizons)
- [ ] Documentation updated (if applicable)

## Adding New Features

### Adding a New Analysis Type

**Example**: Add a "Risk Analysis" view

1. **Create analysis function** in `engelberg/analysis.py`:
   ```python
   def run_risk_analysis(json_path: str) -> dict:
       """Run comprehensive risk analysis."""
       config = load_base_case_config(json_path)

       # Calculate risk metrics
       volatility = calculate_volatility(config)
       value_at_risk = calculate_var(config)

       return {
           'analysis_type': 'risk',
           'volatility': volatility,
           'value_at_risk': value_at_risk,
           'generated_at': datetime.now().isoformat()
       }
   ```

2. **Add JSON export**:
   ```python
   def export_risk_to_json(result: dict, case_name: str):
       output_path = f'website/data/{case_name}_risk.json'
       with open(output_path, 'w', encoding='utf-8') as f:
           json.dump(result, f, indent=2)
   ```

3. **Update batch generator** in `scripts/generate_all_data.py`:
   ```python
   # Add to the analyses loop
   risk_result = run_risk_analysis(assumptions_file)
   export_risk_to_json(risk_result, case_name)
   ```

4. **Add renderer** in `website/index.html`:
   ```javascript
   renderRisk(data) {
       const content = document.getElementById("contentArea");
       content.innerHTML = `
           <h2>Risk Analysis</h2>
           <div class="kpi-grid">
               <div class="kpi-card">
                   <div class="kpi-label">Volatility</div>
                   <div class="kpi-value">${data.volatility.toFixed(2)}%</div>
               </div>
               <!-- More KPIs -->
           </div>
       `;
   }
   ```

5. **Add menu item** in sidebar:
   ```html
   <li data-analysis="risk">
       <i class="fas fa-exclamation-triangle"></i>
       <span>Risk Analysis</span>
   </li>
   ```

6. **Update routing** in `loadAnalysis()`:
   ```javascript
   else if (analysisType === "risk") {
       path = `data/${caseName}_risk.json`;
   }
   ```

7. **Add validation checks** in `scripts/validate_system.py`

### Adding a New Parameter to Sensitivity

**Example**: Add "Tax Rate" sensitivity

1. **Update parameter config** in `engelberg/model_sensitivity_ranges.py`:
   ```python
   MODEL_SENSITIVITY_PARAMETER_CONFIG = [
       # ... existing parameters ...
       {
           'key': 'tax_rate',
           'parameter_name': 'Marginal Tax Rate',
           'range_pct': 20,
           'low_factor': 0.80,
           'high_factor': 1.20,
           'clamp_min': 0.15,
           'clamp_max': 0.45,
           'modifier_fn': 'modify_tax_rate',
           'get_base_value_fn': 'get_tax_rate',
       }
   ]
   ```

2. **Add modifier function** in `engelberg/model_sensitivity.py`:
   ```python
   def modify_tax_rate(base_config, value):
       """Create config with modified tax rate."""
       # Tax rate is passed to compute functions, not in config
       # Return config unchanged, pass value separately
       return base_config
   ```

3. **Update sensitivity loop** to pass tax rate to calculations

4. **Regenerate data**: `python scripts/generate_all_data.py`

### Adding a New Scenario

**Example**: Add "High Interest Rate" scenario

1. **Create assumptions file** `assumptions/assumptions_high_rate.json`:
   ```json
   {
       "_case_metadata": {
           "display_name": "High Interest Rate (3.5%)",
           "description": "Scenario with significantly higher mortgage rate",
           "enabled": true
       },
       "financing": {
           "interest_rate": 0.035
       }
   }
   ```

2. **Generate data**:
   ```bash
   python scripts/generate_all_data.py
   ```

3. **Verify in dashboard**: New case appears in dropdown automatically

## Debugging

### Common Issues

#### Tests Fail After Changes

1. **Check error message**: `python -m pytest tests/ -v`
2. **Run single test**: `python -m pytest tests/unit/test_core_calculations.py::test_name -v`
3. **Add print statements**: Debug values in test
4. **Check fixtures**: Verify test data is correct

#### Dashboard Shows "No data available"

1. **Check console**: Open browser DevTools (F12) and check Console tab
2. **Verify JSON**: Check that `website/data/{case}_{analysis}.json` exists
3. **Check JSON format**: Ensure valid JSON (no trailing commas, proper quotes)
4. **Regenerate data**: `python scripts/generate_all_data.py`

#### Monte Carlo Takes Too Long

1. **Reduce simulations**: Use `--simulations 500` flag
2. **Disable parallel**: Set `use_parallel=False` in code
3. **Profile code**: Use `cProfile` to identify bottlenecks
4. **Optimize hot paths**: Focus on functions called millions of times

#### Validation Fails

1. **Run validation**: `python scripts/validate_system.py`
2. **Read error messages**: They're usually descriptive
3. **Check file structure**: Ensure all required files exist
4. **Verify data**: Check JSON files are valid and complete

### Debugging Tools

#### Python

```bash
# Interactive debugging
python -m pdb scripts/analyze.py

# Profiling
python -m cProfile -o output.prof scripts/analyze.py
python -m pstats output.prof

# Memory profiling
python -m memory_profiler scripts/analyze.py

# Coverage report
python -m pytest --cov=engelberg --cov-report=html tests/
# Opens htmlcov/index.html
```

#### JavaScript

```javascript
// Browser console
console.log("State:", State);
console.log("Data:", State.data);

// Debugger
debugger;  // Pauses execution in DevTools

// Performance
console.time('render');
ChartRenderer.renderMonteCarlo(data);
console.timeEnd('render');
```

## Best Practices

### Python Code

1. **Use dataclasses**: For configuration objects (see `BaseCaseConfig`)
2. **Type hints**: Add type annotations to function signatures
3. **Docstrings**: Document all public functions with Google-style docstrings
4. **Error handling**: Use specific exception types, avoid bare `except:`
5. **File encoding**: Always specify `encoding='utf-8'` when opening files
6. **Immutability**: Don't mutate input parameters; return new objects
7. **Pure functions**: Minimize side effects for easier testing

### JavaScript Code

1. **Use const**: Default to `const`, only use `let` when reassignment needed
2. **Strict equality**: Always use `===` and `!==` (not `==` and `!=`)
3. **Error handling**: Wrap async operations in try-catch
4. **Data validation**: Check for required fields before rendering
5. **Cache data**: Don't reload unchanged data
6. **User feedback**: Show loading states and error messages

### Testing

1. **Test edge cases**: Zero values, negative values, missing data
2. **Test happy path**: Normal expected scenarios
3. **Test error conditions**: Invalid input, missing files
4. **Use fixtures**: Reusable test configurations
5. **Assert precisely**: Check exact values, not just "truthy"

### Documentation

1. **Keep in sync**: Update docs when changing features
2. **Examples**: Include code examples and outputs
3. **Why, not just what**: Explain design decisions
4. **User-focused**: Write for users, not just developers
5. **Update changelog**: Document all notable changes

## Performance Tips

### Python

1. **Vectorize operations**: Use numpy/pandas instead of loops
2. **Profile first**: Don't optimize without measuring
3. **Use generators**: For large datasets, yield instead of return
4. **Cache results**: Memoize expensive calculations
5. **Parallel processing**: Use multiprocessing for independent tasks

### JavaScript

1. **Lazy loading**: Only load data when needed
2. **Debounce events**: Limit rapid-fire event handlers
3. **Cache DOM queries**: Store `getElementById()` results
4. **Minimize reflows**: Batch DOM updates
5. **Use requestAnimationFrame**: For smooth animations

### Data

1. **Compress JSON**: Consider gzip for large files
2. **Reduce precision**: Round values to reasonable precision
3. **Remove redundancy**: Don't duplicate data across files
4. **Lazy load charts**: Only render visible charts

## Contributing Guidelines

### Code Review Checklist

- [ ] Code follows existing style and conventions
- [ ] All tests pass (currently 154/154)
- [ ] System validation passes (currently 403/403)
- [ ] No linter errors
- [ ] Documentation updated
- [ ] CHANGELOG.md updated with changes
- [ ] No bare exception handlers
- [ ] All file operations use UTF-8 encoding
- [ ] No TODO/FIXME comments (create issues instead)
- [ ] Performance is acceptable (profile if needed)

### Commit Message Format

```
<type>: <short description>

<detailed description if needed>

<footer: references, breaking changes, etc.>
```

**Types**: feat, fix, docs, test, refactor, perf, chore

**Examples**:
```
feat: add waterfall chart visualization

Added yearly and monthly waterfall charts showing cash flow bridge
from gross rental income to after-tax cash flow.

- Created ChartRenderer.renderWaterfall()
- Added sidebar menu item
- Updated validation checks
```

```
fix: handle missing data in waterfall charts

Added validation and user-friendly error message when cash flow
data is missing or invalid.
```

## Troubleshooting

### Common Development Issues

#### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'engelberg'`

**Solution**:
- Ensure you're running from project root
- Check Python path: `python -c "import sys; print(sys.path)"`
- Verify `engelberg/__init__.py` exists

#### Path Resolution Errors

**Problem**: `FileNotFoundError: assumptions.json not found`

**Solution**:
- Use `get_project_root()` from `engelberg.core` for path resolution
- Always use absolute paths or project-relative paths
- Run scripts from project root directory

#### Test Failures After Refactoring

**Problem**: Tests fail after code changes

**Solution**:
1. Read error messages carefully
2. Update test fixtures if data structures changed
3. Update expected values if calculation logic changed
4. Add new tests for new functionality

#### Browser Testing Issues

**Problem**: Changes don't appear in browser

**Solution**:
1. Hard refresh: Ctrl+Shift+R (Chrome/Firefox)
2. Clear cache: DevTools -> Application -> Clear Storage
3. Check console for JavaScript errors
4. Verify JSON was regenerated
5. Use cache-busting (already implemented with `?_=${Date.now()}`)

## Advanced Topics

### Adding Correlation to Monte Carlo

To add correlation between two parameters:

1. **Update correlation matrix** in `engelberg/monte_carlo.py`:
   ```python
   correlation_matrix = pd.DataFrame(0.0, index=var_names, columns=var_names)
   np.fill_diagonal(correlation_matrix.values, 1.0)

   # Add your correlation
   correlation_matrix.loc['param1', 'param2'] = 0.5
   correlation_matrix.loc['param2', 'param1'] = 0.5  # Symmetric
   ```

2. **Validate**: Ensure matrix is positive semi-definite

3. **Test**: Run Monte Carlo and verify correlation in results

### Adding a New Distribution Type

To support a new distribution (e.g., Exponential):

1. **Update `DistributionConfig`** to accept new `dist_type`

2. **Add sampling logic** in `latin_hypercube_sample()`:
   ```python
   elif dist.dist_type == 'exponential':
       from scipy.stats import expon
       scale = dist.params['scale']
       samples = expon.ppf(quantiles, scale=scale)
   ```

3. **Add validation** in distribution config checks

4. **Test thoroughly** with known distributions

### Profiling Monte Carlo Performance

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

result = run_monte_carlo_simulation(config, num_simulations=1000)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

**Look for**:
- Functions called millions of times
- High cumulative time
- Opportunities for vectorization

## Release Process

### Version Numbering

Use semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes (e.g., incompatible API changes)
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. **Update version** in relevant files
2. **Update CHANGELOG.md** with all changes since last release
3. **Run full test suite**: `python -m pytest tests/ -v`
4. **Run validation**: `python scripts/validate_system.py`
5. **Regenerate all data**: `python scripts/generate_all_data.py`
6. **Test in browser**: Manual testing of key workflows
7. **Update documentation**: Ensure all docs are current
8. **Create git tag**: `git tag -a v1.2.0 -m "Release 1.2.0"`
9. **Push changes**: `git push && git push --tags`

## Maintenance

### Regular Tasks

**Weekly**:
- Run full test suite
- Check for deprecation warnings
- Review and address TODOs (if any)

**Monthly**:
- Update dependencies: `pip list --outdated`
- Review and update documentation
- Performance profiling
- Security audit

**Quarterly**:
- Dependency major version updates
- Refactoring technical debt
- Architecture review

### Dependency Management

```bash
# Check for updates
pip list --outdated

# Update specific package
pip install --upgrade pandas

# Update requirements file
pip freeze > requirements.txt

# Test after updates
python -m pytest tests/ -v
python scripts/validate_system.py
```

## Resources

### Python Documentation

- **pandas**: https://pandas.pydata.org/docs/
- **numpy**: https://numpy.org/doc/
- **scipy**: https://scipy.org/
- **pytest**: https://docs.pytest.org/

### JavaScript/Web

- **Plotly.js**: https://plotly.com/javascript/
- **MDN Web Docs**: https://developer.mozilla.org/
- **JavaScript Guide**: https://javascript.info/

### Financial Modeling

- **IRR Calculation**: https://en.wikipedia.org/wiki/Internal_rate_of_return
- **Monte Carlo**: https://en.wikipedia.org/wiki/Monte_Carlo_method
- **Latin Hypercube**: https://en.wikipedia.org/wiki/Latin_hypercube_sampling

## Getting Help

### Debugging Steps

1. **Read error message carefully**: Often tells you exactly what's wrong
2. **Check recent changes**: What changed since it last worked?
3. **Isolate the problem**: Minimal reproduction case
4. **Check documentation**: README, CHANGELOG, technical docs
5. **Run validation**: `python scripts/validate_system.py`
6. **Check tests**: Do existing tests cover this case?

### Common Solutions

| Problem | Solution |
|---------|----------|
| Import errors | Check you're in project root, verify paths |
| File not found | Use `get_project_root()`, check file exists |
| Test failures | Read error message, update fixtures if needed |
| Browser issues | Hard refresh, clear cache, check console |
| Slow Monte Carlo | Reduce simulations, disable parallel, profile |
| JSON errors | Validate JSON format, check for trailing commas |

---

**Created**: February 2, 2026
**Purpose**: Development workflow, testing, and contribution guidelines
**Target Audience**: Developers and Contributors
**Status**: Living Document (update as system evolves)
