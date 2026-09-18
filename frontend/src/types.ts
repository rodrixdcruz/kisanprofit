export interface User { id: number; name: string; mobile: string; language: string; is_demo: boolean }
export interface Token { access_token: string; token_type: string; user: User }
export interface Farm { id: number; name: string; area_acres: number; latitude: number | null; longitude: number | null; village: string | null }
export interface Crop { id: number; farm_id: number; name: string; area_acres: number; sowing_date: string | null; expected_yield_quintal: number | null; expected_price_per_quintal: number | null; status: string }
export interface Expense { id: number; crop_id: number | null; category: string; amount: number; spent_on: string; note: string | null; source: string }
export interface Production { id: number; crop_id: number; harvest_date: string; actual_yield_quintal: number; note: string | null }
export interface Sale { id: number; crop_id: number; sale_date: string; quantity_quintal: number; price_per_quintal: number; transport_cost: number; other_charges: number; buyer: string | null }
export interface Dashboard { total_investment: number; total_revenue: number; net_profit: number; roi_percent: number; active_crops: number; total_farms: number; upcoming_harvests: number; pending_sales: number; this_month_expenses: number; largest_category: string | null; largest_category_amount: number }
export interface CropProfit { crop_id: number; crop_name: string; area_acres: number; total_cost: number; revenue: number; profit: number; roi_percent: number; cost_per_acre: number; profit_per_acre: number; break_even_price_per_quintal: number | null; produced_quintal: number; sold_quintal: number; expected_yield_quintal: number | null; production_variance_percent: number | null }
export interface ComparisonRow { crop_name: string; profit: number; roi_percent: number; profit_per_acre: number; is_best: boolean }
export interface Insight { title: string; detail: string; severity: 'info' | 'good' | 'warning' }
export interface ForecastDay { date: string; temp_min_c: number; temp_max_c: number; precipitation_mm: number; precipitation_probability_percent: number; weather_code: number }
export interface Weather { latitude: number; longitude: number; days: ForecastDay[]; advisory: string[]; cached: boolean }
export interface MarketRow { commodity: string; market: string; min_price: number | null; max_price: number | null; modal_price: number | null; price_date: string | null; source: string }
export interface MarketResponse { source: string; live: boolean; rows: MarketRow[]; note?: string }
export interface Notification { id: number; kind: string; title: string; body: string | null; read_at: string | null; created_at: string }
export interface IntegrationStatus { name: string; live: boolean; detail: string }
export interface SimulatorResult { revenue: number; total_cost: number; profit: number; break_even_price_per_quintal: number; sold_out: boolean }
