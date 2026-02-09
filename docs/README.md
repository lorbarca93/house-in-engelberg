# Documentation Index

Welcome to the Engelberg Property Investment Simulation documentation. This index helps you find the right document for your needs.

## Quick Navigation

### Getting Started

| Document | Best For | Time to Read |
|----------|----------|--------------|
| **[../QUICK_START.md](../QUICK_START.md)** | New users, quick setup | 5 minutes |
| **[../README.md](../README.md)** | Comprehensive overview | 15 minutes |

### Technical Reference

| Document | Best For | Time to Read |
|----------|----------|--------------|
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Understanding system design | 10 minutes |
| **[SENSITIVITY_CALCULATIONS.md](SENSITIVITY_CALCULATIONS.md)** | How sensitivity analyses work | 15 minutes |
| **[MONTE_CARLO_ENGINE.md](MONTE_CARLO_ENGINE.md)** | Monte Carlo implementation details | 20 minutes |
| **[WATERFALL_CHARTS.md](WATERFALL_CHARTS.md)** | Interpreting waterfall visualizations | 5 minutes |

### For Developers

| Document | Best For | Time to Read |
|----------|----------|--------------|
| **[DEVELOPMENT.md](DEVELOPMENT.md)** | Setting up dev environment, contributing | 15 minutes |
| **[../BUG_FIX_SUMMARY.md](../BUG_FIX_SUMMARY.md)** | Recent code quality improvements | 5 minutes |
| **[../CHANGELOG.md](../CHANGELOG.md)** | Version history and changes | 20 minutes |

## Documentation by Use Case

### "I want to run the simulation"

1. Read: [QUICK_START.md](../QUICK_START.md)
2. Run: `python scripts/generate_all_data.py`
3. Open: Dashboard in browser

### "I want to understand the results"

1. Read: [README.md](../README.md) -> "Understanding the Results" section
2. Read: [WATERFALL_CHARTS.md](WATERFALL_CHARTS.md) -> Interpretation guide
3. Explore: Dashboard Model Sensitivity and Monte Carlo views

### "I want to add a new scenario"

1. Read: [README.md](../README.md) -> "Configuration" section
2. Create: `assumptions/assumptions_newcase.json`
3. Run: `python scripts/generate_all_data.py`
4. Verify: Dashboard dropdown shows new case

### "I want to understand how calculations work"

1. Read: [ARCHITECTURE.md](ARCHITECTURE.md) -> Data Flow section
2. Read: [SENSITIVITY_CALCULATIONS.md](SENSITIVITY_CALCULATIONS.md)
3. Read: [MONTE_CARLO_ENGINE.md](MONTE_CARLO_ENGINE.md)
4. Review: Code in `engelberg/core.py`

### "I want to contribute code"

1. Read: [DEVELOPMENT.md](DEVELOPMENT.md)
2. Setup: Development environment
3. Test: `python -m pytest tests/ -v`
4. Follow: Pre-commit checklist

### "I want to debug an issue"

1. Read: [DEVELOPMENT.md](DEVELOPMENT.md) -> Debugging section
2. Run: `python scripts/validate_system.py`
3. Check: Error messages and logs
4. Review: [BUG_FIX_SUMMARY.md](../BUG_FIX_SUMMARY.md) for common issues

## Document Overview

### User-Facing Documentation

**QUICK_START.md**
- Commands and quick reference
- Current metrics (base case)
- File structure overview
- Top sensitivity parameters
- 5-10 minute read

**README.md**
- Comprehensive project documentation
- All features and analysis types
- Detailed metric explanations
- Troubleshooting guide
- 15-20 minute read

**WATERFALL_CHARTS.md**
- Waterfall chart guide
- Interpretation tips
- Use cases and examples
- 5 minute read

### Technical Documentation

**ARCHITECTURE.md**
- System architecture diagrams
- Data flow documentation
- Module responsibilities
- Design patterns
- Extension points
- 10-15 minute read

**SENSITIVITY_CALCULATIONS.md**
- Detailed calculation methodology
- Parameter ranges and scaling
- Metric formulas
- Model vs Monte Carlo sensitivity
- 15-20 minute read

**MONTE_CARLO_ENGINE.md**
- Monte Carlo simulation design
- Distribution system
- Sampling methods (LHS, correlations)
- Time-varying parameters (AR(1))
- Event modeling
- Performance optimizations
- 20-25 minute read

### Developer Documentation

**DEVELOPMENT.md**
- Setup instructions
- Development workflow
- Testing strategy
- Code quality guidelines
- Performance tips
- Contributing guidelines
- 15-20 minute read

**BUG_FIX_SUMMARY.md**
- Recent bug fixes
- Code quality improvements
- Testing results
- 5 minute read

**CHANGELOG.md**
- Complete version history
- Feature additions
- Breaking changes
- Migration guides
- 20-30 minute read (reference)

## Documentation Standards

### When to Update Documentation

Update documentation when:

- OK: Adding new features
- OK: Changing existing behavior
- OK: Fixing bugs that affect user experience
- OK: Modifying file structure
- OK: Changing validation check counts
- OK: Adding/removing dependencies

### Documentation Quality Standards

All documentation should:

1. **Be accurate**: Reflect current system state
2. **Be clear**: Use simple language and examples
3. **Be complete**: Cover all important aspects
4. **Be current**: Updated with last-modified date
5. **Be tested**: Examples should actually work

### Documentation Maintenance

**Monthly**:
- Review for accuracy
- Update metrics if base case changed
- Check all code examples still work

**Quarterly**:
- Major review and cleanup
- Reorganize if structure changed
- Add missing sections

**On Release**:
- Update version numbers
- Update CHANGELOG.md
- Verify all examples
- Update "Last Updated" dates

## Getting Help

### Quick Reference

| I need to... | Read... |
|--------------|---------|
| Run the simulation | QUICK_START.md |
| Understand a metric | README.md -> Key Metrics section |
| Interpret a chart | WATERFALL_CHARTS.md or README.md -> Analysis Types |
| Add a new scenario | README.md -> Configuration section |
| Contribute code | DEVELOPMENT.md |
| Understand architecture | ARCHITECTURE.md |
| Learn about sensitivity | SENSITIVITY_CALCULATIONS.md |
| Learn about Monte Carlo | MONTE_CARLO_ENGINE.md |
| See what changed | CHANGELOG.md |
| Debug an issue | DEVELOPMENT.md -> Debugging section |

### Documentation Feedback

If you find documentation issues:

1. **Inaccuracy**: Check if code changed without doc update
2. **Unclear**: Suggest clearer wording
3. **Missing**: Identify gaps in coverage
4. **Out of date**: Check "Last Updated" date vs current code

---

**Created**: February 2, 2026
**Purpose**: Documentation navigation and standards
**Status**: Master index for all documentation

## Summary

The Engelberg Property Investment Simulation has comprehensive documentation covering:

- **8 documentation files** (5,000+ words total)
- **User guides** for quick start and full reference
- **Technical docs** for architecture, calculations, and algorithms
- **Developer guides** for testing, debugging, and contributing
- **Version history** in detailed changelog

All documentation is kept up-to-date with the codebase and validated regularly.
