"""
EcoAudit AI — Test Suite for Energy Calculations

Tests core calculation logic with manually verifiable examples.
Run with: python -m pytest tests/test_energy_calculations.py -v
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.energy_calculations import (
    calculate_daily_consumption_kwh,
    calculate_monthly_consumption_kwh,
    calculate_annual_consumption_kwh,
    calculate_electricity_cost,
    process_appliance_inventory,
    get_consumption_summary,
    get_top_consumers,
    compare_bill_vs_calculated,
    analyze_monthly_bills,
    calculate_savings_for_intervention,
)


class TestDailyConsumption:
    """Tests for calculate_daily_consumption_kwh."""
    
    def test_basic_calculation(self):
        """1000W appliance, 2 units, 5 hours = 2 * 1000 * 5 / 1000 = 10 kWh."""
        result = calculate_daily_consumption_kwh(2, 1000, 5)
        assert result == 10.0
    
    def test_single_unit(self):
        """1 unit, 100W, 10 hours = 1 * 100 * 10 / 1000 = 1 kWh."""
        result = calculate_daily_consumption_kwh(1, 100, 10)
        assert result == 1.0
    
    def test_led_bulb(self):
        """10 LED bulbs at 9W for 6 hours = 10 * 9 * 6 / 1000 = 0.54 kWh."""
        result = calculate_daily_consumption_kwh(10, 9, 6)
        assert abs(result - 0.54) < 0.001
    
    def test_zero_hours(self):
        """Appliance not used: 0 kWh."""
        result = calculate_daily_consumption_kwh(1, 1000, 0)
        assert result == 0.0
    
    def test_zero_power(self):
        """Appliance with 0 watts: 0 kWh."""
        result = calculate_daily_consumption_kwh(1, 0, 10)
        assert result == 0.0
    
    def test_24_hours(self):
        """Refrigerator-style 24h: 1 * 150 * 24 / 1000 = 3.6 kWh."""
        result = calculate_daily_consumption_kwh(1, 150, 24)
        assert abs(result - 3.6) < 0.001
    
    def test_negative_quantity_raises(self):
        with pytest.raises(ValueError):
            calculate_daily_consumption_kwh(-1, 100, 5)
    
    def test_zero_quantity_raises(self):
        with pytest.raises(ValueError):
            calculate_daily_consumption_kwh(0, 100, 5)
    
    def test_negative_power_raises(self):
        with pytest.raises(ValueError):
            calculate_daily_consumption_kwh(1, -100, 5)
    
    def test_negative_hours_raises(self):
        with pytest.raises(ValueError):
            calculate_daily_consumption_kwh(1, 100, -5)
    
    def test_hours_over_24_raises(self):
        with pytest.raises(ValueError):
            calculate_daily_consumption_kwh(1, 100, 25)


class TestMonthlyConsumption:
    """Tests for calculate_monthly_consumption_kwh."""
    
    def test_reference_example(self):
        """The spec reference: 1000W, 2hrs/day, 30 days = 1*1000*2*30/1000 = 60 kWh."""
        result = calculate_monthly_consumption_kwh(1, 1000, 2, 30)
        assert result == 60.0
    
    def test_multiple_units(self):
        """4 fans at 75W, 10hrs, 30 days = 4*75*10*30/1000 = 90 kWh."""
        result = calculate_monthly_consumption_kwh(4, 75, 10, 30)
        assert result == 90.0
    
    def test_partial_month(self):
        """Washing machine: 1*500*1*15/1000 = 7.5 kWh."""
        result = calculate_monthly_consumption_kwh(1, 500, 1, 15)
        assert result == 7.5
    
    def test_zero_days(self):
        result = calculate_monthly_consumption_kwh(1, 1000, 5, 0)
        assert result == 0.0
    
    def test_invalid_days_raises(self):
        with pytest.raises(ValueError):
            calculate_monthly_consumption_kwh(1, 1000, 5, 32)
    
    def test_negative_days_raises(self):
        with pytest.raises(ValueError):
            calculate_monthly_consumption_kwh(1, 1000, 5, -1)


class TestAnnualConsumption:
    """Tests for calculate_annual_consumption_kwh."""
    
    def test_basic_annual(self):
        """60 kWh/month * 12 = 720 kWh/year."""
        result = calculate_annual_consumption_kwh(60.0)
        assert result == 720.0
    
    def test_zero_monthly(self):
        result = calculate_annual_consumption_kwh(0.0)
        assert result == 0.0
    
    def test_negative_monthly_raises(self):
        with pytest.raises(ValueError):
            calculate_annual_consumption_kwh(-10.0)


class TestElectricityCost:
    """Tests for calculate_electricity_cost."""
    
    def test_basic_cost(self):
        """300 kWh at Rs.7/kWh = Rs.2100."""
        result = calculate_electricity_cost(300, 7.0)
        assert result == 2100.0
    
    def test_zero_consumption(self):
        result = calculate_electricity_cost(0, 7.0)
        assert result == 0.0
    
    def test_zero_tariff(self):
        result = calculate_electricity_cost(300, 0.0)
        assert result == 0.0
    
    def test_negative_consumption_raises(self):
        with pytest.raises(ValueError):
            calculate_electricity_cost(-100, 7.0)
    
    def test_negative_tariff_raises(self):
        with pytest.raises(ValueError):
            calculate_electricity_cost(100, -7.0)


class TestApplianceInventory:
    """Tests for process_appliance_inventory."""
    
    def test_empty_inventory(self):
        df = process_appliance_inventory([])
        assert df.empty
        assert 'monthly_kwh' in df.columns
    
    def test_single_appliance(self):
        appliances = [{
            'name': 'Test Bulb',
            'quantity': 1,
            'power_watts': 100,
            'hours_per_day': 10,
            'days_per_month': 30
        }]
        df = process_appliance_inventory(appliances)
        assert len(df) == 1
        assert df.iloc[0]['monthly_kwh'] == 30.0  # 1*100*10*30/1000
        assert df.iloc[0]['percentage_contribution'] == 100.0
    
    def test_two_appliances_percentages(self):
        appliances = [
            {'name': 'A', 'quantity': 1, 'power_watts': 1000, 'hours_per_day': 1, 'days_per_month': 30},
            {'name': 'B', 'quantity': 1, 'power_watts': 1000, 'hours_per_day': 1, 'days_per_month': 30}
        ]
        df = process_appliance_inventory(appliances)
        assert len(df) == 2
        assert df.iloc[0]['percentage_contribution'] == 50.0
        assert df.iloc[1]['percentage_contribution'] == 50.0
    
    def test_invalid_appliance_handled(self):
        """Invalid appliance should not crash, should yield 0 consumption."""
        appliances = [{'name': 'Bad', 'quantity': -1, 'power_watts': 100, 
                       'hours_per_day': 5, 'days_per_month': 30}]
        df = process_appliance_inventory(appliances)
        assert len(df) == 1
        assert df.iloc[0]['monthly_kwh'] == 0.0


class TestConsumptionSummary:
    """Tests for get_consumption_summary."""
    
    def test_empty_df(self):
        import pandas as pd
        df = pd.DataFrame(columns=['daily_kwh', 'monthly_kwh', 'annual_kwh'])
        summary = get_consumption_summary(df, 7.0)
        assert summary['total_monthly_kwh'] == 0.0
        assert summary['monthly_cost_inr'] == 0.0
    
    def test_with_data(self):
        appliances = [
            {'name': 'A', 'quantity': 1, 'power_watts': 1000, 'hours_per_day': 2, 'days_per_month': 30}
        ]
        df = process_appliance_inventory(appliances)
        summary = get_consumption_summary(df, 7.0)
        assert summary['total_monthly_kwh'] == 60.0
        assert summary['total_annual_kwh'] == 720.0
        assert summary['monthly_cost_inr'] == 420.0
        assert summary['annual_cost_inr'] == 5040.0


class TestTopConsumers:
    """Tests for get_top_consumers."""
    
    def test_top_consumers(self):
        appliances = [
            {'name': 'Small', 'quantity': 1, 'power_watts': 10, 'hours_per_day': 1, 'days_per_month': 30},
            {'name': 'Big', 'quantity': 1, 'power_watts': 2000, 'hours_per_day': 8, 'days_per_month': 30},
            {'name': 'Medium', 'quantity': 1, 'power_watts': 500, 'hours_per_day': 4, 'days_per_month': 30},
        ]
        df = process_appliance_inventory(appliances)
        top = get_top_consumers(df, top_n=2)
        assert len(top) == 2
        assert top.iloc[0]['name'] == 'Big'


class TestBillComparison:
    """Tests for compare_bill_vs_calculated."""
    
    def test_calculated_higher(self):
        result = compare_bill_vs_calculated(500, 400)
        assert result['calculated_higher'] is True
        assert result['absolute_difference_kwh'] == 100.0
        assert result['percentage_difference'] == 25.0  # 100/400 * 100
    
    def test_billed_higher(self):
        result = compare_bill_vs_calculated(300, 400)
        assert result['calculated_higher'] is False
        assert result['absolute_difference_kwh'] == 100.0
    
    def test_equal(self):
        result = compare_bill_vs_calculated(400, 400)
        assert result['absolute_difference_kwh'] == 0.0
    
    def test_zero_billed(self):
        result = compare_bill_vs_calculated(400, 0)
        assert result['percentage_difference'] == 100.0  # 400/400 * 100
    
    def test_both_zero(self):
        result = compare_bill_vs_calculated(0, 0)
        assert result['percentage_difference'] == 0.0


class TestMonthlyBills:
    """Tests for analyze_monthly_bills."""
    
    def test_empty_bills(self):
        result = analyze_monthly_bills({})
        assert 'error' in result
    
    def test_single_month(self):
        result = analyze_monthly_bills({'January': 300}, tariff=7.0)
        assert result['months_available'] == 1
        assert result['average_monthly_kwh'] == 300.0
        assert result['is_complete_year'] is False
    
    def test_full_year(self):
        bills = {m: 300 for m in ['January', 'February', 'March', 'April', 'May', 'June',
                                   'July', 'August', 'September', 'October', 'November', 'December']}
        result = analyze_monthly_bills(bills, tariff=7.0)
        assert result['months_available'] == 12
        assert result['is_complete_year'] is True
        assert result['total_for_period_kwh'] == 3600.0
        assert result['estimated_period_cost_inr'] == 25200.0
    
    def test_varying_bills(self):
        bills = {'January': 200, 'February': 400, 'March': 300}
        result = analyze_monthly_bills(bills, tariff=7.0)
        assert result['highest_month'] == 'February'
        assert result['lowest_month'] == 'January'
        assert result['average_monthly_kwh'] == 300.0
    
    def test_null_values_ignored(self):
        bills = {'January': 300, 'February': None, 'March': 0}
        result = analyze_monthly_bills(bills, tariff=7.0)
        assert result['months_available'] == 1


class TestSavingsCalculation:
    """Tests for calculate_savings_for_intervention."""
    
    def test_basic_savings(self):
        """100 kWh baseline, 20% reduction = 20 kWh/month saved."""
        result = calculate_savings_for_intervention(100, 0.20, tariff=7.0)
        assert result['monthly_kwh_saved'] == 20.0
        assert result['annual_kwh_saved'] == 240.0
        assert result['monthly_cost_saved_inr'] == 140.0
        assert result['annual_cost_saved_inr'] == 1680.0
    
    def test_zero_reduction(self):
        result = calculate_savings_for_intervention(100, 0.0, tariff=7.0)
        assert result['monthly_kwh_saved'] == 0.0
    
    def test_full_reduction(self):
        result = calculate_savings_for_intervention(100, 1.0, tariff=7.0)
        assert result['monthly_kwh_saved'] == 100.0
    
    def test_invalid_reduction_raises(self):
        with pytest.raises(ValueError):
            calculate_savings_for_intervention(100, 1.5, tariff=7.0)
    
    def test_negative_reduction_raises(self):
        with pytest.raises(ValueError):
            calculate_savings_for_intervention(100, -0.1, tariff=7.0)
    
    def test_negative_baseline_raises(self):
        with pytest.raises(ValueError):
            calculate_savings_for_intervention(-100, 0.20, tariff=7.0)
    
    def test_with_implementation_cost(self):
        result = calculate_savings_for_intervention(100, 0.20, tariff=7.0, implementation_cost=2000)
        assert result['implementation_cost_inr'] == 2000
        # Payback: 2000 / 140 = 14.3 months
        assert abs(result['payback_months'] - 14.3) < 0.1
    
    def test_zero_savings_with_cost(self):
        result = calculate_savings_for_intervention(0, 0.20, tariff=7.0, implementation_cost=1000)
        assert result['payback_months'] is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
