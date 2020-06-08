#pragma once

#ifndef _MSC_VER
extern "C" {
#include <csim/update_ops.h>
}
#else
#include <csim/update_ops.h>
#endif

#include "gate_named.hpp"
#include "state.hpp"

/**
 * \~japanese-en CNOTゲート
 */
class ClsCNOTGate : public QuantumGate_OneControlOneTarget{
public:
    /**
     * \~japanese-en コンストラクタ
     * 
     * @param control_qubit_index コントロール量子ビットの添え字
     * @param target_qubit_index ターゲット量子ビットの添え字
     */
    ClsCNOTGate(UINT control_qubit_index, UINT target_qubit_index) {
        this->_update_func = CNOT_gate;
		this->_update_func_dm = dm_CNOT_gate;
#ifdef _USE_GPU
		this->_update_func_gpu = CNOT_gate_host;
#endif
        this->_name = "CNOT";
        this->_target_qubit_list.push_back(TargetQubitInfo(target_qubit_index, FLAG_X_COMMUTE ));
        this->_control_qubit_list.push_back(ControlQubitInfo(control_qubit_index, 1 ));
        this->_gate_property = FLAG_CLIFFORD;
        this->_matrix_element = ComplexMatrix::Zero(2,2);
        this->_matrix_element << 0,1,1,0;
    }
};

/**
 * \~japanese-en Control-Zゲート
 */
class ClsCZGate : public QuantumGate_OneControlOneTarget {
public:
    /**
     * \~japanese-en コンストラクタ
     * 
     * @param control_qubit_index コントロール量子ビットの添え字
     * @param target_qubit_index ターゲット量子ビットの添え字
     */
    ClsCZGate(UINT control_qubit_index, UINT target_qubit_index) {
        this->_update_func = CZ_gate;
		this->_update_func_dm = dm_CZ_gate;
#ifdef _USE_GPU
		this->_update_func_gpu = CZ_gate_host;
#endif
        this->_name = "CZ";
        this->_target_qubit_list.push_back(TargetQubitInfo(target_qubit_index, FLAG_Z_COMMUTE ));
        this->_control_qubit_list.push_back(ControlQubitInfo(control_qubit_index, 1 ));
        this->_gate_property = FLAG_CLIFFORD;
        this->_matrix_element = ComplexMatrix::Zero(2,2);
        this->_matrix_element << 1,0,0,-1;
    }
};

/**
 * \~japanese-en Control-Rゲート(dummy)
 */
class ClsCRGate : public QuantumGate_OneControlOneTarget {
protected:
    double _angle;

public:
    /**
     * \~japanese-en コンストラクタ
     * 
     * @param control_qubit_index コントロール量子ビットの添え字
     * @param target_qubit_index ターゲット量子ビットの添え字
     */
    ClsCRGate(UINT control_qubit_index, UINT target_qubit_index, double angle) : _angle(angle) {
        this->_update_func = NULL;
		this->_update_func_dm = NULL;
#ifdef _USE_GPU
		this->_update_func_gpu = NULL;
#endif
        this->_name = "CR";
        this->_target_qubit_list.push_back(TargetQubitInfo(target_qubit_index, FLAG_Z_COMMUTE ));
        this->_control_qubit_list.push_back(ControlQubitInfo(control_qubit_index, 1 ));
        this->_gate_property = FLAG_CLIFFORD;
        this->_matrix_element = ComplexMatrix::Zero(2,2);
        this->_matrix_element << 1,0,0,-1;
    }
    /**
     * \~japanese-en 自身のディープコピーを生成する
     * 
     * @return 自身のディープコピー
     */
    virtual QuantumGateBase* copy() const override {
        auto gate = new ClsCRGate(*this);
        gate->_angle = this->_angle;
        return gate;
    };
    /**
     * \~japanese-en 回転角を返す
     * 
     * @return 回転角
     */
    virtual double get_parameter() const {
      return this->_angle;
    }
};

/**
 * \~japanese-en SWAPゲート
 */
class ClsSWAPGate : public QuantumGate_TwoQubit{
public:
    /**
     * \~japanese-en コンストラクタ
     * 
     * @param target_qubit_index1 ターゲット量子ビットの添え字
     * @param target_qubit_index2 もう一つのターゲット量子ビットの添え字
     */
    ClsSWAPGate(UINT target_qubit_index1, UINT target_qubit_index2) {
        this->_update_func = SWAP_gate;
		this->_update_func_dm = dm_SWAP_gate;
#ifdef _USE_GPU
		this->_update_func_gpu = SWAP_gate_host;
#endif
        this->_name = "SWAP";
        this->_target_qubit_list.push_back(TargetQubitInfo(target_qubit_index1, 0 ));
        this->_target_qubit_list.push_back(TargetQubitInfo(target_qubit_index2, 0 ));
        this->_gate_property = FLAG_CLIFFORD;
        this->_matrix_element = ComplexMatrix::Zero(4,4);
        this->_matrix_element << 1,0,0,0 , 0,0,1,0 , 0,1,0,0 , 0,0,0,1;
    }
};
