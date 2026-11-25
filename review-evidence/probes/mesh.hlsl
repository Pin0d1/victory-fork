struct Vertex { float4 pos : SV_Position; };
[RootSignature("")]
[outputtopology("triangle")]
[numthreads(1,1,1)]
void ms(out vertices Vertex v[3], out indices uint3 t[1]) {
    SetMeshOutputCounts(3,1);
    v[0].pos=float4(-1,-1,0.5,1); v[1].pos=float4(-1,3,0.5,1); v[2].pos=float4(3,-1,0.5,1);
    t[0]=uint3(0,1,2);
}
[RootSignature("")]
float4 ps() : SV_Target { return float4(0,1,0,1); }
