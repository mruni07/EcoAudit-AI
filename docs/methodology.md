# EcoAudit AI — Methodology Document

## 1. Energy Audit Workflow

EcoAudit AI follows a structured preliminary energy audit workflow:

1. **Data Collection** — User provides building profile, appliance inventory, and electricity bill data.
2. **Consumption Estimation** — Appliance-level energy consumption is calculated using standard formulas.
3. **Bill Comparison** — Calculated consumption is compared with actual billed consumption.
4. **Finding Generation** — Audit findings are categorized by data confidence level.
5. **Envelope Screening** — Qualitative building envelope assessment based on user descriptions.
6. **Intervention Analysis** — Potential energy-saving measures are evaluated with estimated savings.
7. **Report Generation** — A comprehensive PDF report is generated from the user's data.

## 2. Appliance Consumption Formulas

### Daily Energy Consumption
```
Daily kWh = Quantity × Rated Power (W) × Hours Used per Day ÷ 1000
```

### Monthly Energy Consumption
```
Monthly kWh = Quantity × Rated Power (W) × Hours per Day × Days per Month ÷ 1000
```

### Annual Energy Consumption
```
Annual kWh = Monthly kWh × 12
```
**Assumption:** Monthly usage pattern is assumed constant throughout the year.

### Electricity Cost
```
Cost (₹) = Consumption (kWh) × Tariff (₹/kWh)
```

## 3. Key Assumptions

| Assumption | Explanation |
|-----------|-------------|
| Rated power as proxy | The nameplate rated power is used to estimate consumption. Actual average draw may be lower for thermostat-controlled appliances (ACs, refrigerators, water heaters) due to duty cycles. |
| Constant monthly pattern | Annual consumption is extrapolated from monthly data, assuming no seasonal variation. |
| Flat tariff rate | A single flat tariff is used. Actual utility tariffs may use slab-based pricing, time-of-day rates, or seasonal rates. |
| Usage hours | Hours per day are user-estimated averages, not based on continuous monitoring or metering. |
| Appliance independence | Each appliance's consumption is calculated independently. Interactions (e.g., waste heat from lighting increasing AC load) are not modelled. |

## 4. Measured vs. Estimated Consumption

| Data Type | Source | Confidence |
|-----------|--------|------------|
| Billed consumption | Electricity meter / utility bill | High — actual measurement |
| Appliance consumption | Calculated from rated power × usage | Medium — based on assumptions |
| Savings estimates | Assumed reduction percentages | Low — general estimates |
| Building envelope observations | User descriptions | Low — not verified by inspection |

The application clearly labels each data type so users can assess confidence.

## 5. Bill vs. Calculated Comparison

When both calculated and billed consumption are available:

- **Absolute difference** = |Calculated − Billed|
- **Percentage difference** = Absolute difference ÷ Billed × 100%

The application does NOT force these to match. Discrepancies are explained with possible reasons.

## 6. Energy-Saving Interventions

For each intervention:
```
Estimated Monthly Savings (kWh) = Baseline Consumption × Reduction Fraction
Estimated Cost Savings (₹/month) = Energy Saved × Tariff
Payback Period = Implementation Cost ÷ Monthly Savings
```

**The reduction fraction is an adjustable assumption, not a guaranteed outcome.**

Users can edit the reduction percentage and implementation cost for each intervention.

## 7. Building Code References

Code references are selected based on:
1. **Relevance** — Direct applicability to residential buildings in India.
2. **Authority** — Published by BEE, BIS, or other official bodies.
3. **Verification** — Each reference includes edition, issuing authority, and official source link.
4. **Limitations** — Applicability constraints are clearly stated.

The application does NOT:
- Verify code compliance.
- Invent specific clause numbers or threshold values.
- Claim that publication equals mandatory applicability in all states.

## 8. AI-Generated Responses

AI chatbot responses are:
- Provided for educational and informational purposes.
- Not a substitute for professional advice.
- Based on the current audit context when available.
- Clearly labelled as AI-generated (full mode) or curated (demo mode).

The AI is instructed to:
- Distinguish estimates from measured data.
- Avoid inventing official code references.
- Recommend professional assessment when appropriate.
- Not guarantee savings outcomes.

## 9. Limitations

1. This is a preliminary screening tool, not a professional energy audit.
2. Consumption estimates may differ significantly from actual consumption.
3. Building envelope assessment is qualitative, not based on thermal simulation.
4. Savings estimates are approximate and not guaranteed.
5. Code references are for awareness; formal compliance requires professional assessment.
6. The tool does not monitor or measure actual energy consumption.
