@@ .. @@
# Include travel router (if available)
if travel_router:
    app.include_router(travel_router)

+# Include dynamic agent router
+try:
+    from api.dynamic_agent_endpoints import router as dynamic_router
+    app.include_router(dynamic_router)
+except ImportError:
+    dynamic_router = None
+
 # ✅ Globalsh
 memory_manager = MemoryManager()