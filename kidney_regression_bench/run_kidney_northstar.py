from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from neokidney import KidneyParameters,KidneyState,calculate_kidney_state
from neorenalcoupling import run_cv_kidney,run_cvlung_kidney
from neolung import LungParameters
from neolung.gas_exchange import GasExchangeParameters

standalone=calculate_kidney_state(KidneyParameters(),KidneyState(),map_mmhg=52,cvp_mmhg=4,systemic_flow_ml_min=800)
cv=run_cv_kidney()
cvl=run_cvlung_kidney()
peep=run_cvlung_kidney(lung_params=LungParameters(peep_cmh2o=8.0))
hyp=run_cvlung_kidney(gas_params=GasExchangeParameters(fio2=0.12))
out={
 "schema":"Kidney Integration NorthStar v1",
 "standalone":{"rbf":standalone.renal_flow_ml_min,"uo":standalone.urine_ml_kg_hr},
 "cv":{"map":cv.circulation_metrics.mean_aortic_mmhg,"co":cv.circulation_metrics.native_output_ml_min,
       "rbf":cv.kidney.renal_flow_ml_min,"uo":cv.kidney.urine_ml_kg_hr},
 "cvlung":{"map":cvl.circulation_metrics.mean_aortic_mmhg,"co":cvl.circulation_metrics.native_output_ml_min,
           "pao2":cvl.gas_pao2_mmhg,"rbf":cvl.kidney.renal_flow_ml_min,"uo":cvl.kidney.urine_ml_kg_hr},
 "peep8":{"map":peep.circulation_metrics.mean_aortic_mmhg,"rbf":peep.kidney.renal_flow_ml_min,"uo":peep.kidney.urine_ml_kg_hr},
 "hypoxia":{"map":hyp.circulation_metrics.mean_aortic_mmhg,"pao2":hyp.gas_pao2_mmhg,
            "rbf":hyp.kidney.renal_flow_ml_min,"uo":hyp.kidney.urine_ml_kg_hr}
}
p=ROOT/"kidney_regression_bench"/"current_kidney_northstar.json"
p.write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
