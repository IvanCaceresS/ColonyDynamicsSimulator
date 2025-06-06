#if UNITY_EDITOR
using UnityEngine;
using UnityEditor;
using System.IO;
using System.Collections.Generic;
public static class PrefabMaterialCreator
{
    const string pF="Assets/Resources/Prefabs",mF="Assets/Resources/PrefabsMaterials",meshF="Assets/Resources/PrefabsMeshes";
    [MenuItem("Tools/Create Prefabs and Materials")]
    public static void CreatePrefabsAndMaterials()
    {
        DeleteAndRecreateAllAssetFolders();
        AssetDatabase.Refresh();
        Debug.Log($"Folders checked/created: Prefabs='{Path.GetFullPath(pF)}', Materials='{Path.GetFullPath(mF)}', Meshes='{Path.GetFullPath(meshF)}'");
        //CODE START
        
        //CODE END
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("Prefab and material creation process completed.");
    }
    private static void DeleteAndRecreateAllAssetFolders()
    {
        string[] foldersToManage = { pF, mF, meshF };
        foreach (string folderPath in foldersToManage)
        {
            if (Directory.Exists(folderPath)) Directory.Delete(folderPath, true);
            Directory.CreateDirectory(folderPath);
        }
    }
    static void CPAM_Primitive(string n, PrimitiveType t, Vector3 s, Vector3 r, int ct, Color c)
    {
        GameObject o = GameObject.CreatePrimitive(t);
        o.name = n;
        o.transform.rotation = Quaternion.Euler(r);
        o.transform.localScale = s;
        if (o.TryGetComponent<Collider>(out var dC)) Object.DestroyImmediate(dC);
        if (ct == 0) o.AddComponent<SphereCollider>();
        else if (ct == 1) o.AddComponent<CapsuleCollider>();
        var sh = Shader.Find("Universal Render Pipeline/Lit");
        if (sh == null)
        {
            Debug.LogError($"Shader URP/Lit not found for {n}. Material will not be created.");
            Object.DestroyImmediate(o);
            return;
        }
        Material m = new Material(sh) { name = n + "_Material", color = c };
        string mP = Path.Combine(mF, m.name + ".mat");
        AssetDatabase.CreateAsset(m, mP);
        o.GetComponent<Renderer>().sharedMaterial = m;
        string pP = Path.Combine(pF, n + ".prefab");
        PrefabUtility.SaveAsPrefabAsset(o, pP);
        Object.DestroyImmediate(o);
        Debug.Log($"Prefab '{n}' created at '{pP}' with material '{mP}'");
    }
    static void CPAM_Helical(string name, float axialLength, Vector3 rotation, Color color)
    {
        axialLength = Mathf.Clamp(axialLength, 5f, 30f);

        float helixRadius = 0.5f;
        float tubeRadius = 0.1f;
        float totalTurns = axialLength * 0.3f;
        
        int segmentsAlongHelix = Mathf.Clamp((int)(axialLength * 3), 10, 500);
        int segmentsAroundTube = Mathf.Clamp((int)(axialLength * 1.5f), 5, 50);

        if (segmentsAlongHelix < 2 || segmentsAroundTube < 3)
        {
            Debug.LogError($"Los segmentos calculados son insuficientes para generar la malla '{name}'. Se requieren al menos 2 segmentos de hélice y 3 de tubo.");
            return;
        }

        GameObject HeliGO = new GameObject(name);
        HeliGO.transform.rotation = Quaternion.Euler(rotation); // Apply rotation
        MeshFilter meshFilter = HeliGO.AddComponent<MeshFilter>();
        MeshRenderer meshRenderer = HeliGO.AddComponent<MeshRenderer>();
        Mesh mesh = new Mesh { name = name + "_GeneratedMesh" };
        List<Vector3> vertices = new List<Vector3>();
        List<int> triangles = new List<int>();
        List<Vector2> uvs = new List<Vector2>();

        float yIncrement = axialLength / (segmentsAlongHelix - 1);
        float fullCircleRad = 2 * Mathf.PI;
        float angularStepPerUnitY = totalTurns * fullCircleRad / axialLength; 
        
        for (int i = 0; i < segmentsAlongHelix; i++)
        {
            float currentY = -axialLength / 2.0f + i * yIncrement;
            float helixAngle = currentY * angularStepPerUnitY;
            Vector3 ringCenter = new Vector3(helixRadius * Mathf.Cos(helixAngle), currentY, helixRadius * Mathf.Sin(helixAngle));
            Vector3 tangent = new Vector3(-helixRadius * angularStepPerUnitY * Mathf.Sin(helixAngle), 1.0f, helixRadius * angularStepPerUnitY * Mathf.Cos(helixAngle)).normalized;
            Vector3 normal = Mathf.Abs(Vector3.Dot(tangent, Vector3.up)) > 0.999f ? Quaternion.AngleAxis(helixAngle * Mathf.Rad2Deg, Vector3.up) * Vector3.right : Vector3.Cross(tangent, Vector3.up).normalized;
            Vector3 binormal = Vector3.Cross(tangent, normal).normalized;
            for (int j = 0; j < segmentsAroundTube; j++)
            {
                float tubeSegmentAngle = (float)j / segmentsAroundTube * fullCircleRad;
                Vector3 vertOffset = (normal * Mathf.Cos(tubeSegmentAngle) + binormal * Mathf.Sin(tubeSegmentAngle)) * tubeRadius;
                vertices.Add(ringCenter + vertOffset);
                uvs.Add(new Vector2((float)j / segmentsAroundTube, (float)i / (segmentsAlongHelix - 1f)));
            }
        }

        for (int i = 0; i < segmentsAlongHelix - 1; i++)
        {
            for (int j = 0; j < segmentsAroundTube; j++)
            {
                int r1c1 = i * segmentsAroundTube + j;
                int r1c2 = i * segmentsAroundTube + (j + 1) % segmentsAroundTube;
                int r2c1 = (i + 1) * segmentsAroundTube + j;
                int r2c2 = (i + 1) * segmentsAroundTube + (j + 1) % segmentsAroundTube;
                triangles.Add(r1c1); triangles.Add(r2c1); triangles.Add(r1c2);
                triangles.Add(r1c2); triangles.Add(r2c1); triangles.Add(r2c2);
            }
        }
        
        string meshAssetPath = "";
        if (vertices.Count > 0 && triangles.Count > 0)
        {
            mesh.vertices = vertices.ToArray(); mesh.triangles = triangles.ToArray(); mesh.uv = uvs.ToArray();
            mesh.RecalculateNormals(); mesh.RecalculateBounds();
            if (!Directory.Exists(meshF)) Directory.CreateDirectory(meshF);
            meshAssetPath = Path.Combine(meshF, mesh.name + ".asset");
            AssetDatabase.CreateAsset(mesh, meshAssetPath);
            Debug.Log($"Mesh for {name} generated and saved at '{meshAssetPath}': Vertices={mesh.vertexCount}, Triangles={mesh.triangles.Length / 3}");
        }
        else
        {
            Debug.LogError($"Generated mesh for {name} is empty! Vertices={vertices.Count}, Triangles={triangles.Count}");
            Object.DestroyImmediate(HeliGO); return;
        }
        
        Mesh loadedMesh = AssetDatabase.LoadAssetAtPath<Mesh>(meshAssetPath);
        meshFilter.sharedMesh = loadedMesh ? loadedMesh : mesh;
        
        var sh = Shader.Find("Universal Render Pipeline/Lit");
        if (sh == null) { Debug.LogError($"Shader URP/Lit not found for {name}. Material will not be created."); Object.DestroyImmediate(HeliGO); return; }
        
        Material matInstanceHeli = new Material(sh) { name = name + "_Material", color = color };
        if (!Directory.Exists(mF)) Directory.CreateDirectory(mF);
        string materialPathHeli = Path.Combine(mF, matInstanceHeli.name + ".mat");
        AssetDatabase.CreateAsset(matInstanceHeli, materialPathHeli);
        
        Material loadedMaterialHeli = AssetDatabase.LoadAssetAtPath<Material>(materialPathHeli);
        meshRenderer.sharedMaterial = loadedMaterialHeli ? loadedMaterialHeli : matInstanceHeli;
        
        CapsuleCollider placeholderCollider = HeliGO.AddComponent<CapsuleCollider>();
        placeholderCollider.radius = helixRadius + tubeRadius;
        placeholderCollider.height = axialLength;
        placeholderCollider.direction = 1; 
        
        if (!Directory.Exists(pF)) Directory.CreateDirectory(pF);
        string prefabPathHeli = Path.Combine(pF, name + ".prefab");
        PrefabUtility.SaveAsPrefabAsset(HeliGO, prefabPathHeli);
        Object.DestroyImmediate(HeliGO);
        Debug.Log($"Prefab '{name}' created in '{prefabPathHeli}' with mesh '{meshAssetPath}' and material '{materialPathHeli}'");
    }
}
#endif