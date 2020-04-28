import xml.etree.ElementTree as ET

def objl_read(filename):
    tree = ET.parse(filename)
    objl_xml = tree.getroot()

    objl = []
    for p in range(len(objl_xml)):
        # Mandatory attributes:
        lbl = int(objl_xml[p].get('class_label'))
        x = float(objl_xml[p].get('x'))
        y = float(objl_xml[p].get('y'))
        z = float(objl_xml[p].get('z'))

        # Optional attributes:
        tidx = objl_xml[p].get('tomo_idx')
        objid = objl_xml[p].get('obj_id')
        psi = objl_xml[p].get('psi')
        phi = objl_xml[p].get('phi')
        the = objl_xml[p].get('the')
        csize = objl_xml[p].get('cluster_size')

        # if optional attributes exist, then cast to correct type:
        if tidx != None:
            tidx = int(tidx)
        if objid != None:
            objid = int(objid)
        if csize != None:
            csize = int(csize)
        if psi != None or phi != None or the != None:
            psi = float(psi)
            phi = float(phi)
            the = float(the)

        obj = {
            'tomo_idx': tidx,
            'obj_id': objid,
            'label': lbl,
            'x': x,
            'y': y,
            'z': z,
            'psi': phi,
            'phi': psi,
            'the': the,
            'cluster_size': csize
        }

        objl.append(obj)
    return objl

def objl_get_labels(objl):
    """
    Returns a list with different (unique) labels contained in input objl
    """
    class_list = []
    for idx in range(len(objl)):
        class_list.append(objl[idx]['label'])
    # Set only stores a value once even if it is inserted more then once:
    lbl_set  = set(class_list) # insert the list to the set
    lbl_list = (list(lbl_set)) # convert the set to the list
    return lbl_list

def objl_get_class(objl, label):
    """
    Get all objects of specified class.

    Args:
        objl (list of dict)
        label (int)
    Returns:
        list of dict: contains only objects from class 'label'
    """
    idx_class = []
    for idx in range(len(objl)):
        if str(objl[idx]['label'])==str(label):
            idx_class.append(idx)

    objlOUT = []
    for idx in range(len(idx_class)):
        objlOUT.append(objl[idx_class[idx]])
    return objlOUT