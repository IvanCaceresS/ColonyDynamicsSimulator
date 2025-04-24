#if UNITY_EDITOR
using UnityEngine;
using UnityEditor;
using System.IO;

public static class PrefabMaterialCreator
{
    const string pF="Assets/Resources/Prefabs",mF="Assets/Resources/PrefabsMaterials";
    [MenuItem("Tools/Crear Prefabs y Materiales")]public static void CreatePrefabsAndMaterials()
    {
        if(!AssetDatabase.IsValidFolder(pF))
        {
            AssetDatabase.CreateFolder("Assets/Resources","Prefabs");
            Debug.Log("Carpeta creada: "+pF);
        }
        if(!AssetDatabase.IsValidFolder(mF))
        {
            AssetDatabase.CreateFolder("Assets/Resources","PrefabsMaterials");
            Debug.Log("Carpeta creada: "+mF);
        }
        CPAM("SCerevisiae",PrimitiveType.Sphere,new Vector3(5,5,5),new Vector3(90,0,0),0);
        CPAM("EColi",PrimitiveType.Capsule,new Vector3(.5f,1,.5f),new Vector3(90,0,0),1);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("Prefabs y materiales creados.");
    }
    static void CPAM(string n,PrimitiveType t,Vector3 s,Vector3 r,int c)
    {
        var o=GameObject.CreatePrimitive(t);
        o.name=n;
        o.transform.rotation=Quaternion.Euler(r);
        o.transform.localScale=s;
        var col=o.GetComponent<Collider>();
        if(col!=null)Object.DestroyImmediate(col);
        if(c==0)o.AddComponent<SphereCollider>();
        else o.AddComponent<CapsuleCollider>();
        var sh=Shader.Find("Universal Render Pipeline/Lit");
        if(sh==null)
        {
            Debug.LogError("Shader URP/Lit no encontrado.");
            return;
        }
        var m=new Material(sh);
        m.color=n=="SCerevisiae"?new Color(0.5f,0.25f,0,1):n=="EColi"?new Color(1,0.975f,0.25f,1):Color.white;
        AssetDatabase.CreateAsset(m,Path.Combine(mF,n+".mat"));
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        o.GetComponent<Renderer>().sharedMaterial=m;
        PrefabUtility.SaveAsPrefabAsset(o,Path.Combine(pF,n+".prefab"));
        Object.DestroyImmediate(o);
    }
}
#endif
