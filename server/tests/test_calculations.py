from datetime import date
from types import SimpleNamespace
from app.utils.eco_calculations import compute_eco_fields

def row(gap):
    base=date(2026,1,1)
    attrs=dict(hq_eco_release_date=base,az_eco_register_date=base,az_eco_creation_date=base,second_aprov_rd_finish_1=date(2026,1,1+gap),hz_sh_in_receive_date_1=None,hz_sh_in_receive_date_2=None,hz_sh_in_receive_date_3=None,agreement_start_1=None,agreement_finish_1=None,agreement_start_2=None,agreement_finish_2=None,agreement_start_3=None,agreement_finish_3=None,second_aprov_rd_start_1=None,second_aprov_rd_start_2=None,second_aprov_rd_finish_2=None)
    return SimpleNamespace(**attrs)
def test_gap_14_boundary():
    assert compute_eco_fields(row(14))['contar_eco_14'] is False
    assert compute_eco_fields(row(15))['contar_eco_14'] is True
