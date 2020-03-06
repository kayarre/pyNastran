from __future__ import annotations
from typing import TYPE_CHECKING
import numpy as np

from pyNastran.nptyping import NDArrayNfloat
from pyNastran.dev.solver.utils import lambda1d, get_ieids_eids
from pyNastran.dev.solver.build_stiffness import ke_cbar
from pyNastran.op2.op2_interface.hdf5_interface import (
    RealSpringStrainArray, RealRodStrainArray,
    RealBarStrainArray,
)
if TYPE_CHECKING:  # pragma: no cover
    from pyNastran.bdf.bdf import BDF, CBAR, PBAR, PBARL


def recover_strain_101(f06_file, op2,
                       model: BDF, dof_map, isubcase: int, xb, fdtype: str='float32',
                       title: str='', subtitle: str='', label: str='',
                       page_num: int=1, page_stamp: str='PAGE %s'):
    """
    recovers the strains from:
     - STRAIN= ALL

    """
    eid_str = 'ALL'
    nelements = 0
    nelements += _recover_strain_celas(
        f06_file, op2, model, dof_map, isubcase, xb, eid_str,
        'CELAS1', fdtype=fdtype,
        title=title, subtitle=subtitle, label=label,
        page_num=page_num, page_stamp=page_stamp)
    nelements += _recover_strain_celas(
        f06_file, op2, model, dof_map, isubcase, xb, eid_str,
        'CELAS2', fdtype=fdtype,
        title=title, subtitle=subtitle, label=label,
        page_num=page_num, page_stamp=page_stamp)
    nelements += _recover_strain_celas(
        f06_file, op2, model, dof_map, isubcase, xb, eid_str,
        'CELAS3', fdtype=fdtype,
        title=title, subtitle=subtitle, label=label,
        page_num=page_num, page_stamp=page_stamp)
    nelements += _recover_strain_celas(
        f06_file, op2, model, dof_map, isubcase, xb, eid_str,
        'CELAS4', fdtype=fdtype,
        title=title, subtitle=subtitle, label=label,
        page_num=page_num, page_stamp=page_stamp)

    nelements += _recover_strain_rod(
        f06_file, op2, model, dof_map, isubcase, xb, eid_str,
        'CROD', fdtype=fdtype,
        title=title, subtitle=subtitle, label=label,
        page_num=page_num, page_stamp=page_stamp)
    nelements += _recover_strain_rod(
        f06_file, op2, model, dof_map, isubcase, xb, eid_str,
        'CONROD', fdtype=fdtype,
        title=title, subtitle=subtitle, label=label,
        page_num=page_num, page_stamp=page_stamp)
    nelements += _recover_strain_rod(
        f06_file, op2, model, dof_map, isubcase, xb, eid_str,
        'CTUBE', fdtype=fdtype,
        title=title, subtitle=subtitle, label=label,
        page_num=page_num, page_stamp=page_stamp)
    nelements += _recover_strain_bar(
        f06_file, op2, model, dof_map, isubcase, xb, eid_str,
        'CBAR', fdtype=fdtype,
        title=title, subtitle=subtitle, label=label,
        page_num=page_num, page_stamp=page_stamp)


    #assert nelements > 0, nelements
    if nelements == 0:
        model.log.warning(f'no strain output...{model.card_count}')

def _recover_strain_celas(f06_file, op2,
                          model: BDF, dof_map, isubcase, xg, eids_str,
                          element_name: str, fdtype='float32',
                          title: str='', subtitle: str='', label: str='',
                          page_num: int=1, page_stamp='PAGE %s') -> None:
    """recovers static spring strain"""
    neids, ielas, eids, strains = get_ieids_eids(model, element_name, eids_str, fdtype=fdtype)
    if not neids:
        return neids
    if element_name == 'CELAS1':
        for ieid, eid in zip(ielas, eids):
            elem = model.elements[eid]
            si = elem.pid_ref.s
            strains[ieid] = _recover_straini_celas12(xg, dof_map, elem, si)
    elif element_name == 'CELAS2':
        for ieid, eid in zip(ielas, eids):
            elem = model.elements[eid]
            si = elem.s
            strains[ieid] = _recover_straini_celas12(xg, dof_map, elem, si)
    elif element_name == 'CELAS3':
        for ieid, eid in zip(ielas, eids):
            elem = model.elements[eid]
            si = elem.pid_ref.s
            strains[ieid] = _recover_straini_celas34(xg, dof_map, elem, si)
    elif element_name == 'CELAS4':
        for ieid, eid in zip(ielas, eids):
            elem = model.elements[eid]
            si = 1.0 # TODO: is this right?
            strains[ieid] = _recover_straini_celas34(xg, dof_map, elem, si)
    else:  # pragma: no cover
        raise NotImplementedError(element_name)

    data = strains.reshape(1, *strains.shape)
    table_name = 'OSTR1'
    spring_strain = RealSpringStrainArray.add_static_case(
        table_name, element_name, eids, data, isubcase, is_stress=False,
        is_sort1=True, is_random=False, is_msc=True,
        random_code=0, title=title, subtitle=subtitle, label=label)
    if element_name == 'CELAS1':
        op2.celas1_strain[isubcase] = spring_strain
    elif element_name == 'CELAS2':
        op2.celas2_strain[isubcase] = spring_strain
    elif element_name == 'CELAS3':
        op2.celas3_strain[isubcase] = spring_strain
    elif element_name == 'CELAS4':
        op2.celas4_strain[isubcase] = spring_strain
    else:  # pragma: no cover
        raise NotImplementedError(element_name)
    spring_strain.write_f06(f06_file, header=None, page_stamp=page_stamp,
                            page_num=page_num, is_mag_phase=False, is_sort1=True)
    return neids


def _recover_strain_rod(f06_file, op2,
                        model: BDF, dof_map, isubcase, xb, eids_str,
                        element_name, fdtype='float32',
                        title: str='', subtitle: str='', label: str='',
                        page_num: int=1, page_stamp='PAGE %s') -> None:
    """recovers static rod strain"""
    neids, irod, eids, strains = get_ieids_eids(model, element_name, eids_str,
                                                ncols=4, fdtype=fdtype)
    if not neids:
        return neids
    if element_name == 'CONROD':
        for ieid, eid in zip(irod, eids):
            elem = model.elements[eid]
            strains[ieid, :] = _recover_straini_rod(xb, dof_map, elem, elem)
    elif element_name == 'CROD':
        for ieid, eid in zip(irod, eids):
            elem = model.elements[eid]
            strains[ieid, :] = _recover_straini_rod(xb, dof_map, elem, elem.pid_ref)
    elif element_name == 'CTUBE':
        for ieid, eid in zip(irod, eids):
            elem = model.elements[eid]
            strains[ieid, :] = _recover_straini_ctube(xb, dof_map, elem, elem.pid_ref)
    else:  # pragma: no cover
        raise NotImplementedError(element_name)

    data = strains.reshape(1, *strains.shape)
    table_name = 'OSTR1'
    strain_obj = RealRodStrainArray.add_static_case(
        table_name, element_name, eids, data, isubcase, is_stress=False,
        is_sort1=True, is_random=False, is_msc=True,
        random_code=0, title=title, subtitle=subtitle, label=label)

    if element_name == 'CONROD':
        op2.conrod_strain[isubcase] = strain_obj
    elif element_name == 'CROD':
        op2.crod_strain[isubcase] = strain_obj
    elif element_name == 'CTUBE':
        op2.ctube_strain[isubcase] = strain_obj
    else:  # pragma: no cover
        raise NotImplementedError(element_name)

    strain_obj.write_f06(f06_file, header=None, page_stamp=page_stamp,
                         page_num=page_num, is_mag_phase=False, is_sort1=True)
    return neids

def _recover_straini_celas12(xg, dof_map, elem, si: float):
    """get the static spring strain"""
    nid1, nid2 = elem.nodes
    c1, c2 = elem.c1, elem.c2
    i = dof_map[(nid1, c1)]
    j = dof_map[(nid2, c2)]
    strain = xg[j] - xg[i]  # TODO: check the sign
    # TODO: why is the strain 0?
    return si * strain

def _recover_straini_celas34(xg, dof_map, elem, si: float):
    """get the static spring strain"""
    nid1, nid2 = elem.nodes
    i = dof_map[(nid1, 0)]
    j = dof_map[(nid2, 0)]
    strain = xg[j] - xg[i]  # TODO: check the sign
    # TODO: why is the strain 0?
    return si * strain

def _recover_straini_rod(xb, dof_map, elem, prop):
    """get the static rod strain"""
    nid1, nid2 = elem.nodes

    # axial
    i11 = dof_map[(nid1, 1)]
    i12 = i11 + 1
    i13 = i11 + 2

    i21 = dof_map[(nid2, 1)]
    i22 = i21 + 1
    i23 = i21 + 2

    # torsion
    i14 = i11 + 3
    i15 = i11 + 4
    i16 = i11 + 5

    i24 = i21 + 3
    i25 = i21 + 4
    i26 = i21 + 5

    q_axial = np.array([
        xb[i11], xb[i12], xb[i13],
        xb[i21], xb[i22], xb[i23],
    ])
    q_torsion = np.array([
        xb[i14], xb[i15], xb[i16],
        xb[i24], xb[i25], xb[i26],
    ])
    xyz1 = elem.nodes_ref[0].get_position()
    xyz2 = elem.nodes_ref[1].get_position()
    dxyz12 = xyz1 - xyz2
    Lambda = lambda1d(dxyz12, debug=False)

    u_axial = Lambda @ q_axial
    u_torsion = Lambda @ q_torsion
    du_axial = u_axial[0] - u_axial[1]
    du_torsion = u_torsion[0] - u_torsion[1]
    #headers = ['axial', 'SMa', 'torsion', 'SMt']

    C = prop.c

    xyz1 = elem.nodes_ref[0].get_position()
    xyz2 = elem.nodes_ref[1].get_position()
    dxyz12 = xyz1 - xyz2
    L = np.linalg.norm(dxyz12)

    axial_strain = du_axial / L
    torsional_strain = du_torsion * C / L

    return axial_strain, np.nan, torsional_strain, np.nan

def _recover_straini_ctube(xb, dof_map, elem, prop):
    """get the static ctube strain"""
    nid1, nid2 = elem.nodes

    # axial
    i11 = dof_map[(nid1, 1)]
    i12 = i11 + 1
    i13 = i11 + 2

    i21 = dof_map[(nid2, 1)]
    i22 = i21 + 1
    i23 = i21 + 2

    # torsion
    i14 = i11 + 3
    i15 = i11 + 4
    i16 = i11 + 5

    i24 = i21 + 3
    i25 = i21 + 4
    i26 = i21 + 5

    q_axial = np.array([
        xb[i11], xb[i12], xb[i13],
        xb[i21], xb[i22], xb[i23],
    ])
    q_torsion = np.array([
        xb[i14], xb[i15], xb[i16],
        xb[i24], xb[i25], xb[i26],
    ])
    xyz1 = elem.nodes_ref[0].get_position()
    xyz2 = elem.nodes_ref[1].get_position()
    dxyz12 = xyz1 - xyz2
    Lambda = lambda1d(dxyz12, debug=False)

    u_axial = Lambda @ q_axial
    u_torsion = Lambda @ q_torsion
    du_axial = u_axial[0] - u_axial[1]
    du_torsion = u_torsion[0] - u_torsion[1]
    #headers = ['axial', 'SMa', 'torsion', 'SMt']

    xyz1 = elem.nodes_ref[0].get_position()
    xyz2 = elem.nodes_ref[1].get_position()
    dxyz12 = xyz1 - xyz2
    L = np.linalg.norm(dxyz12)

    axial_strain = du_axial / L
    torsional_strain = du_torsion / L

    return axial_strain, np.nan, torsional_strain, np.nan

def _recover_strain_bar(f06_file, op2,
                        model: BDF, dof_map, isubcase, xb, eids_str,
                        element_name, fdtype='float32',
                        title: str='', subtitle: str='', label: str='',
                        page_num: int=1, page_stamp='PAGE %s') -> None:
    """recovers static rod strain"""
    neids, irod, eids, strains = get_ieids_eids(model, element_name, eids_str,
                                                ncols=15, fdtype=fdtype)
    if not neids:
        return neids

    if element_name == 'CBAR':
        for ieid, eid in zip(irod, eids):
            elem = model.elements[eid]
            #[s1a, s2a, s3a, s4a, axial, smaxa, smina, MS_tension,
            # s1b, s2b, s3b, s4b,        sminb, sminb, MS_compression] - 15
            strains[ieid, :] = _recover_straini_cbar(model, xb, dof_map, elem, elem.pid_ref)
    else:  # pragma: no cover
        raise NotImplementedError(element_name)

    data = strains.reshape(1, *strains.shape)
    table_name = 'OSTR1'

    strain_obj = RealBarStrainArray.add_static_case(
        table_name, element_name, eids, data, isubcase, is_stress=False,
        is_sort1=True, is_random=False, is_msc=True,
        random_code=0, title=title, subtitle=subtitle, label=label)

    if element_name == 'CBAR':
        op2.cbar_strain[isubcase] = strain_obj
    else:  # pragma: no cover
        raise NotImplementedError(element_name)

    strain_obj.write_f06(f06_file, header=None, page_stamp=page_stamp,
                         page_num=page_num, is_mag_phase=False, is_sort1=True)
    return neids

def _recover_straini_cbar(model: BDF, xb: NDArrayNfloat,
                          dof_map,
                          elem: CBAR, prop: Union[PBAR, PBARL], fdtype='float64'):
    """get the static bar strain"""
    nid1, nid2 = elem.nodes

    # axial
    i1 = dof_map[(nid1, 1)]
    j1 = dof_map[(nid2, 1)]

    q_all = np.hstack([
        xb[i1:i1+6],
        xb[j1:j1+6],
    ])
    print(len(xb[i1:i1+3],))
    q_axial = np.hstack([
        xb[i1:i1+3],
        xb[j1:j1+3],
    ])
    print(q_axial)
    q_torsion = np.hstack([
        xb[i1+3:i1+6],
        xb[j1+3:j1+6],
    ])
    #{F} = [K]{u}

    nid1, nid2 = elem.nodes
    is_passed, Ke = ke_cbar(model, elem, fdtype=fdtype)
    assert is_passed

    pid_ref = elem.pid_ref
    mat = pid_ref.mid_ref

    #is_passed, (wa, wb, ihat, jhat, khat) = elem.get_axes(model)
    #T = np.vstack([ihat, jhat, khat])
    #z = np.zeros((3, 3), dtype='float64')
    prop = elem.pid_ref
    #mat = prop.mid_ref
    I1 = prop.I11()
    I2 = prop.I22()
    A = prop.Area()
    J = prop.J()
    unused_I12 = prop.I12()

    Fe = Ke @ q_all
    (Fx1, Fy1, Fz1, Mx1, My1, Mz1,
    Fx2, Fy2, Fz2, Mx2, My2, Mz2) = Fe
    s_axial = Fx1 / A
    s_torsion = Mx1 / J

    xyz1 = elem.nodes_ref[0].get_position()
    xyz2 = elem.nodes_ref[1].get_position()
    #dxyz12 = xyz1 - xyz2
    #Lambda = lambda1d(dxyz12, debug=False)

    #u_axial = Lambda @ q_axial
    #u_torsion = Lambda @ q_torsion
    #du_axial = u_axial[0] - u_axial[1]
    #du_torsion = u_torsion[0] - u_torsion[1]

    xyz1 = elem.nodes_ref[0].get_position()
    xyz2 = elem.nodes_ref[1].get_position()
    dxyz12 = xyz1 - xyz2
    L = np.linalg.norm(dxyz12)
    Lambda = lambda1d(dxyz12, debug=False)

    u_axial = Lambda @ q_axial
    u_torsion = Lambda @ q_torsion
    du_axial = u_axial[0] - u_axial[1]
    du_torsion = u_torsion[0] - u_torsion[1]


    axial = du_axial / L

    # cdef = prop.get_cdef()
    if prop.type == 'PBARL':
        # these axes are backwards...
        #     ^ y
        # +---|---+
        # |   |   |
        # |   +------> z
        # |       |
        # +-------+
        if prop.Type in ['ROD', 'TUBE']:
            R = prop.dims[0]
            cdef = np.array([
                [R, 0.],
                [0., R],
                [-R, 0.],
                [0., -R],
            ], dtype='float64')
        elif prop.Type in ['BAR', 'BOX']:
            height, width = prop.dims
            cdef = np.array([
                [width, height],
                [width, -height],
                [-width, -height],
                [-width, height],
            ], dtype='float64') / 2.
        else:
            raise NotImplementedError(prop.Type)
    elif prop.type == 'PBAR':
        cdef = np.array([
                [prop.c1, prop.c2],
                [prop.d1, prop.d2],
                [prop.e1, prop.e2],
                [prop.f1, prop.f2],
            ], dtype='float64')
    else:
        raise NotImplementedError(prop.get_stats())
    model.log.info(f'cdef: {cdef}\n')

    Iy = I1
    Iz = I2
    G = mat.G()
    E = mat.E()
    strains = []
    for (T, My, Mz) in [(Mx1, My1, Mz1), (Mx2, My2, Mz2)]:
        for yz in cdef:
            y, z = yz
            radius = np.linalg.norm(yz)
            unused_torsional_stress = (T * radius) / J
            unused_phi = (T * L) / (G * J)

            stress = My * y / Iy + Mz * z / Iy
            strain = stress / E
            strains.append(strain)

    s1a = strains[0]
    s2a = strains[1]
    s3a = strains[2]
    s4a = strains[3]
    s1b = strains[4]
    s2b = strains[5]
    s3b = strains[6]
    s4b = strains[7]
    smaxa = max(s1a, s2a, s3a, s4a)
    smaxb = max(s1b, s2b, s3b, s4b)

    smina = min(s1a, s2a, s3a, s4a)
    sminb = min(s1b, s2b, s3b, s4b)
    MS_tension = MS_compression = np.nan
    out = (
        s1a, s2a, s3a, s4a, axial, smaxa, smina, MS_tension,
        s1b, s2b, s3b, s4b,        sminb, sminb, MS_compression) # 15
    return out