package com.example.frontbackweb;

import org.junit.jupiter.api.Test;
import at.favre.lib.crypto.bcrypt.BCrypt;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class PasswordHashTest {
    
    @Test
    public void testAdminPasswordHash() {
        // This is the correct hash from data.sql that we verified works
        String storedHash = "$2a$10$DxDjxrTikQBAybXht4EgXuM1MsdbgSfoUkFqp0bD4Oo.KXq6ht5Uy";
        String password = "admin123";
        
        BCrypt.Result result = BCrypt.verifyer().verify(password.toCharArray(), storedHash);
        
        assertTrue(result.verified, "Password 'admin123' should match the stored hash");
    }
} 